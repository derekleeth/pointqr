"""WebSocket endpoint that streams live Celery / RabbitMQ telemetry to admin clients.

Architecture:
  - A single background asyncio task polls the RabbitMQ Management HTTP API
    and the Celery inspect API on a configurable interval.
  - Collected metrics are pushed into an asyncio.Queue shared by the broadcaster.
  - A broadcaster coroutine drains that queue and fans the payload out to every
    connected WebSocket client.
  - Clients authenticate via a JWT access-token sent as a query-parameter
    (?token=…) because the WebSocket handshake does not support custom headers
    in most browsers.

Environment variables consumed (all optional, sensible defaults provided):
  RABBITMQ_MGMT_URL   – Base URL of the Management plugin  (default: http://rabbitmq:15672)
  RABBITMQ_MGMT_USER  – Management API username            (default: guest)
  RABBITMQ_MGMT_PASS  – Management API password            (default: guest)
  METRICS_INTERVAL_S  – Poll interval in seconds           (default: 3)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx
from celery import Celery
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.celery_app import celery_app
from app.core.security import decode_access_token
from app.models.user import UserRole

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin-ws"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RABBITMQ_MGMT_URL: str = os.getenv("RABBITMQ_MGMT_URL", "http://rabbitmq:15672")
RABBITMQ_MGMT_USER: str = os.getenv("RABBITMQ_MGMT_USER", "pointqr")
RABBITMQ_MGMT_PASS: str = os.getenv("RABBITMQ_MGMT_PASS", "pointqr_dev_password")
METRICS_INTERVAL_S: float = float(os.getenv("METRICS_INTERVAL_S", "3"))

# Maximum number of metric frames buffered before back-pressure is applied.
_QUEUE_MAX: int = 20


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------

@dataclass
class ConnectionManager:
    """Tracks active WebSocket connections and broadcasts messages."""

    _connections: set[WebSocket] = field(default_factory=set)

    def connect(self, ws: WebSocket) -> None:
        self._connections.add(ws)
        logger.info("WS client connected. Total: %d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.info("WS client disconnected. Total: %d", len(self._connections))

    async def broadcast(self, payload: dict[str, Any]) -> None:
        """Fan-out a JSON payload to all connected clients, dropping dead ones."""
        if not self._connections:
            return
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.discard(ws)

    @property
    def client_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
_metric_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=_QUEUE_MAX)
_poller_task: asyncio.Task | None = None
_broadcaster_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# Metric collectors
# ---------------------------------------------------------------------------

async def _fetch_rabbitmq_metrics(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Pull per-queue depth from the RabbitMQ Management API.

    Returns a list of dicts with keys: name, ready, unacked, total.
    Returns [] on any error so the poller continues gracefully.
    """
    try:
        resp = await client.get(
            f"{RABBITMQ_MGMT_URL}/api/queues/%2F",
            auth=(RABBITMQ_MGMT_USER, RABBITMQ_MGMT_PASS),
            timeout=5.0,
        )
        resp.raise_for_status()
        queues = resp.json()
        return [
            {
                "name": q.get("name", "unknown"),
                "ready": q.get("messages_ready", 0),
                "unacked": q.get("messages_unacknowledged", 0),
                "total": q.get("messages", 0),
            }
            for q in queues
            # Filter to the four queues this app actually uses
            if q.get("name") in {"default", "qr_export", "qr_batch", "scan_analytics"}
        ]
    except Exception as exc:
        logger.debug("RabbitMQ metrics unavailable: %s", exc)
        return []


def _fetch_celery_stats() -> dict[str, int]:
    """Query active Celery workers via the inspect API (synchronous, fast).

    Returns counts per logical state: active, reserved, scheduled, revoked.
    Falls back to zeros if no workers are reachable within the timeout.
    """
    inspect = celery_app.control.inspect(timeout=2.0)
    result: dict[str, int] = {"active": 0, "reserved": 0, "scheduled": 0, "revoked": 0}
    try:
        active = inspect.active() or {}
        for tasks in active.values():
            result["active"] += len(tasks)

        reserved = inspect.reserved() or {}
        for tasks in reserved.values():
            result["reserved"] += len(tasks)

        scheduled = inspect.scheduled() or {}
        for tasks in scheduled.values():
            result["scheduled"] += len(tasks)

        revoked = inspect.revoked() or {}
        for tasks in revoked.values():
            result["revoked"] += len(tasks)

    except Exception as exc:
        logger.debug("Celery inspect unavailable: %s", exc)

    return result


# ---------------------------------------------------------------------------
# Background poller – runs as a long-lived asyncio Task
# ---------------------------------------------------------------------------

async def _run_poller() -> None:
    """Continuously collect metrics and enqueue snapshots for the broadcaster."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # Run the blocking Celery inspect in a thread so we don't
                # stall the event loop.
                celery_stats = await asyncio.get_event_loop().run_in_executor(
                    None, _fetch_celery_stats
                )
                queue_depths = await _fetch_rabbitmq_metrics(client)

                snapshot: dict[str, Any] = {
                    "ts": datetime.now(tz=timezone.utc).isoformat(),
                    "queues": queue_depths,
                    "celery": celery_stats,
                }

                # Non-blocking put; drop oldest if the queue is full (back-pressure)
                if _metric_queue.full():
                    try:
                        _metric_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await _metric_queue.put(snapshot)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Unexpected error in metrics poller: %s", exc)

            await asyncio.sleep(METRICS_INTERVAL_S)


async def _run_broadcaster() -> None:
    """Drain the metric queue and fan out to all WebSocket clients."""
    while True:
        try:
            snapshot = await _metric_queue.get()
            if manager.client_count > 0:
                await manager.broadcast(snapshot)
            _metric_queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Unexpected error in metrics broadcaster: %s", exc)


# ---------------------------------------------------------------------------
# Lifecycle helpers – called from main.py lifespan
# ---------------------------------------------------------------------------

def start_metrics_background_tasks() -> None:
    """Spawn the poller and broadcaster tasks.  Call once from app lifespan."""
    global _poller_task, _broadcaster_task
    loop = asyncio.get_event_loop()
    _poller_task = loop.create_task(_run_poller(), name="metrics-poller")
    _broadcaster_task = loop.create_task(_run_broadcaster(), name="metrics-broadcaster")
    logger.info("Metrics background tasks started (interval=%.1fs)", METRICS_INTERVAL_S)


def stop_metrics_background_tasks() -> None:
    """Cancel the background tasks gracefully.  Call from app lifespan shutdown."""
    for task in (_poller_task, _broadcaster_task):
        if task and not task.done():
            task.cancel()
    logger.info("Metrics background tasks cancelled")


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/metrics")
async def metrics_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
) -> None:
    """Stream live queue-depth and Celery task-state telemetry.

    Clients must pass a valid admin JWT via the `token` query parameter because
    the browser WebSocket API does not support custom request headers.

    Message format (JSON):
    {
      "ts": "<ISO-8601 UTC timestamp>",
      "queues": [
        { "name": "default", "ready": 12, "unacked": 3, "total": 15 },
        ...
      ],
      "celery": {
        "active": 5, "reserved": 2, "scheduled": 0, "revoked": 1
      }
    }
    """
    # ── Auth: validate token before upgrading the connection ──────────────
    try:
        token_data = decode_access_token(token)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify the token subject encodes an admin user.
    # We do a lightweight check here; the user object is loaded only to
    # confirm the role claim persisted in the DB matches.
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == token_data.sub))
        user = result.scalar_one_or_none()

    if user is None or not user.is_active or user.role != UserRole.admin:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ── Upgrade connection ────────────────────────────────────────────────
    await websocket.accept()
    manager.connect(websocket)

    # Send a handshake frame immediately so the client knows it's connected.
    await websocket.send_json({"type": "connected", "interval_s": METRICS_INTERVAL_S})

    try:
        # Keep alive: discard any client-sent frames (ping / pong / close).
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
