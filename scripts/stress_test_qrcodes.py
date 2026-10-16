#!/usr/bin/env python3
"""PointQR API & Celery Queue Stress Testing Script.

Generates diverse QR codes with different styling features, dot patterns,
corner shapes, color themes, and outer labels, then optionally triggers
asynchronous Celery vector/raster export jobs to stress-test backend workers
and RabbitMQ task queues back-to-back.

Uses Python standard library only (no third-party dependencies required).

Command-Line Arguments & Flags:
================================================================================
Authentication:
  -k, --api-key <KEY>
      Personal PointQR API key passed in the 'X-API-Key' HTTP header.
      If omitted, reads from the POINTQR_API_KEY environment variable.
  --auto-login <EMAIL:PASSWORD | EMAIL>
      Authenticate with credentials and automatically retrieve or generate
      a personal API key.
      NOTE ON BASH '!' HISTORY EXPANSION:
      If your password contains an exclamation point (e.g., BippityBopBoo123!),
      Bash will try to expand '!123' as a history command, resulting in:
          bash: !123: event not found
      To avoid this, either:
        1. Wrap the argument in SINGLE QUOTES:
           --auto-login 'admin@pointqr.dev:BippityBopBoo123!'
        2. Use separate --email and let the script prompt securely:
           --email admin@pointqr.dev
        3. Set environment variables:
           export POINTQR_PASSWORD='BippityBopBoo123!'
  --email <EMAIL>
      User email for auto-authentication (or env var POINTQR_EMAIL).
  --password <PASSWORD>
      User password (or env var POINTQR_PASSWORD). If omitted when --email is
      supplied, you will be prompted securely without showing characters.

Load & Concurrency:
  -n, --count <INT>
      Total number of QR codes to generate (default: 10).
  -c, --concurrency <INT>
      Number of parallel worker threads executing requests back-to-back (default: 5).
  --delay <FLOAT>
      Optional staggered delay in seconds between thread starts (default: 0.0).

Target & Payloads:
  -u, --url <URL>
      Base API URL without trailing slash (default: 'http://localhost/api').
  --type {mixed,static,dynamic}
      QR code type to generate (default: 'mixed').
      - 'mixed'   : Alternates between STATIC and DYNAMIC codes.
      - 'static'  : Static QR codes encoding direct URLs.
      - 'dynamic' : Dynamic QR codes with short codes and redirect tracking.

Celery Export Queue ('qr_export'):
  --export (default) / --no-export
      Dispatch an asynchronous Celery export task for every created QR code.
  --format {random,png,svg,pdf,eps}
      File format for Celery render worker (default: 'random').
  --poll (default) / --no-poll
      Poll '/v1/qrcodes/jobs/{id}' until Celery finishes rendering and report latency.
      Use --no-poll for fire-and-forget Celery task dispatch.
  --poll-timeout <FLOAT>
      Maximum time in seconds to wait for a Celery BatchJob to complete (default: 15.0).
  --poll-interval <FLOAT>
      Interval in seconds between export status polling requests (default: 0.5).

Celery Scan Analytics Queue ('scan_analytics'):
  --simulate-scans
      Hit dynamic QR redirect endpoints ('/r/{short_code}') to stress-test the
      background 'log_scan_event' Celery task queue and atomic scan increments.

Rate Limiting & Network:
  --rotate-ips (default)
      Rotate simulated client IPs in 'CF-Connecting-IP' and 'X-Forwarded-For'
      headers to bypass the 30 req/min slowapi IP limiter during high-volume runs.

Display & Debugging:
  --no-color
      Disable ANSI terminal colors in output.
  --dry-run
      Print sample styled JSON payloads and exit without sending network requests.

Usage Examples:
================================================================================
  # Basic test generating 10 styled QR codes and Celery export jobs:
  python3 scripts/stress_test_qrcodes.py --api-key <KEY> -n 10

  # High-volume stress test with 50 QR codes across 10 threads with job polling:
  python3 scripts/stress_test_qrcodes.py -k <KEY> -n 50 -c 10 --poll

  # Stress-test both Celery queues ('qr_export' + 'scan_analytics'):
  python3 scripts/stress_test_qrcodes.py -k <KEY> -n 20 -c 5 --simulate-scans

  # Auto-login with SINGLE QUOTES to prevent Bash exclamation mark expansion:
  python3 scripts/stress_test_qrcodes.py --auto-login 'admin@pointqr.dev:BippityBopBoo123!' -n 25

  # Auto-login with secure interactive password prompt (never exposed in shell history):
  python3 scripts/stress_test_qrcodes.py --email admin@pointqr.dev -n 25

  # Dry-run preview of generated styles:
  python3 scripts/stress_test_qrcodes.py --dry-run -n 5
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# ANSI Terminal Colors
# ---------------------------------------------------------------------------
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def c(text: str, color: str, enabled: bool = True) -> str:
    """Format text with ANSI color code if enabled."""
    return f"{color}{text}{Colors.RESET}" if enabled else text


# ---------------------------------------------------------------------------
# Style Palettes & Preset Themes
# ---------------------------------------------------------------------------
DOT_TYPES = [
    "square",
    "dots",
    "rounded",
    "classy",
    "classy-rounded",
    "extra-rounded",
]

CORNER_SQUARE_TYPES = ["square", "dot", "extra-rounded"]
CORNER_DOT_TYPES = ["square", "dot"]
ERROR_CORRECTION_LEVELS = ["L", "M", "Q", "H"]
EXPORT_FORMATS = ["png", "svg", "pdf", "eps"]

COLOR_THEMES = [
    {
        "name": "Midnight Tech",
        "dots": "#0f172a",
        "corner_square": "#1e3a8a",
        "corner_dot": "#2563eb",
        "bg": "#ffffff",
        "label": "#0f172a",
    },
    {
        "name": "Emerald Eco",
        "dots": "#065f46",
        "corner_square": "#047857",
        "corner_dot": "#10b981",
        "bg": "#f0fdf4",
        "label": "#065f46",
    },
    {
        "name": "Crimson Ruby",
        "dots": "#991b1b",
        "corner_square": "#b91c1c",
        "corner_dot": "#dc2626",
        "bg": "#fffbeb",
        "label": "#7f1d1d",
    },
    {
        "name": "Cyber Purple",
        "dots": "#6d28d9",
        "corner_square": "#4c1d95",
        "corner_dot": "#7c3aed",
        "bg": "#faf5ff",
        "label": "#5b21b6",
    },
    {
        "name": "Sunset Amber",
        "dots": "#c2410c",
        "corner_square": "#ea580c",
        "corner_dot": "#f97316",
        "bg": "#fff7ed",
        "label": "#9a3412",
    },
    {
        "name": "Ocean Teal",
        "dots": "#0f766e",
        "corner_square": "#0e7490",
        "corner_dot": "#06b6d4",
        "bg": "#f0fdfa",
        "label": "#134e4a",
    },
    {
        "name": "Berry Velvet",
        "dots": "#831843",
        "corner_square": "#9d174d",
        "corner_dot": "#db2777",
        "bg": "#fff1f2",
        "label": "#700735",
    },
    {
        "name": "Slate Minimal",
        "dots": "#334155",
        "corner_square": "#1e293b",
        "corner_dot": "#475569",
        "bg": "#f8fafc",
        "label": "#1e293b",
    },
    {
        "name": "Classic Monochrome",
        "dots": "#000000",
        "corner_square": "#000000",
        "corner_dot": "#000000",
        "bg": "#ffffff",
        "label": "#000000",
    },
]

TOP_LABELS = [
    "SCAN ME",
    "VISIT WEBSITE",
    "EXCLUSIVE OFFER",
    "MENU & ORDER",
    "WI-FI ACCESS",
    "POINTQR DEMO",
    "FAST CHECK-IN",
    "TABLE RESERVATION",
    "EVENT PASS",
    "DOWNLOAD APP",
]

BOTTOM_LABELS = [
    "POWERED BY POINTQR",
    "VALID UNTIL 2027",
    "POINT CAMERA HERE",
    "SECURE VERIFIED QR",
    "LIMITED TIME ONLY",
    "TAP NOTIFICATION",
    "HIGH RESOLUTION ASSET",
    "VIP MEMBER ACCESS",
]


# ---------------------------------------------------------------------------
# Results & Telemetry Data Structures
# ---------------------------------------------------------------------------
@dataclass
class QRResult:
    index: int
    qr_id: Optional[str] = None
    title: str = ""
    qr_type: str = ""
    short_code: Optional[str] = None
    style_theme: str = ""
    dot_type: str = ""
    create_status: int = 0
    create_latency_ms: float = 0.0
    create_error: Optional[str] = None

    # Celery Export Task
    export_format: Optional[str] = None
    job_id: Optional[str] = None
    export_status: Optional[str] = None
    export_latency_ms: float = 0.0
    export_error: Optional[str] = None
    download_url: Optional[str] = None

    # Dynamic Scan
    scan_status: Optional[int] = None
    scan_latency_ms: float = 0.0


@dataclass
class TestSummary:
    total_requested: int = 0
    created_success: int = 0
    created_failed: int = 0
    rate_limited: int = 0
    export_dispatched: int = 0
    export_completed: int = 0
    export_failed: int = 0
    scans_dispatched: int = 0
    scans_success: int = 0
    total_duration_s: float = 0.0
    results: List[QRResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HTTP Helper
# ---------------------------------------------------------------------------
class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Handler that intercepts 3xx redirect status without following outbound target URL."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_no_redirect_opener = urllib.request.build_opener(_NoRedirectHandler)


def make_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
    follow_redirects: bool = True,
) -> Tuple[int, Dict[str, Any], float]:
    """Execute HTTP request using urllib. Returns (status_code, response_json_or_dict, elapsed_ms)."""
    headers = headers or {}
    encoded_data = None
    if data is not None:
        encoded_data = json.dumps(data).encode("utf-8")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    start_time = time.perf_counter()

    opener = urllib.request.urlopen if follow_redirects else _no_redirect_opener.open

    try:
        with opener(req, timeout=timeout) as response:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            status_code = response.status
            raw_body = response.read().decode("utf-8")
            try:
                body = json.loads(raw_body) if raw_body else {}
            except json.JSONDecodeError:
                body = {"raw": raw_body}
            return status_code, body, elapsed_ms
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        # If code is 302/301 and we chose not to follow redirects, that's a success
        if not follow_redirects and e.code in (301, 302, 307, 308):
            return e.code, {"location": e.headers.get("Location")}, elapsed_ms

        raw_body = e.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            body = {"detail": raw_body}
        return e.code, body, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return 0, {"detail": str(e)}, elapsed_ms


# ---------------------------------------------------------------------------
# Style Payload Generator
# ---------------------------------------------------------------------------
def generate_qr_payload(index: int, qr_type_preference: str = "mixed") -> Tuple[Dict[str, Any], str, str]:
    """Build a distinct QR payload with varying styles, labels, and geometry."""
    theme = COLOR_THEMES[index % len(COLOR_THEMES)]
    dot_type = DOT_TYPES[index % len(DOT_TYPES)]
    corner_sq_type = CORNER_SQUARE_TYPES[index % len(CORNER_SQUARE_TYPES)]
    corner_dot_type = CORNER_DOT_TYPES[index % len(CORNER_DOT_TYPES)]
    ec_level = ERROR_CORRECTION_LEVELS[index % len(ERROR_CORRECTION_LEVELS)]

    # Determine static vs dynamic
    if qr_type_preference == "static":
        qr_type = "STATIC"
    elif qr_type_preference == "dynamic":
        qr_type = "DYNAMIC"
    else:  # mixed: alternate
        qr_type = "STATIC" if (index % 2 == 0) else "DYNAMIC"

    target_url = f"https://example.com/pointqr/stress-test/{index}?ts={int(time.time())}"

    # Labels configuration: Alternate between top label, bottom label, both, or none
    label_mode = index % 4
    has_top = label_mode in (0, 2)
    has_bottom = label_mode in (1, 2)

    top_text = TOP_LABELS[index % len(TOP_LABELS)]
    bottom_text = BOTTOM_LABELS[index % len(BOTTOM_LABELS)]

    # Size variations (300, 350, 400, 450, 500)
    sizes = [300, 350, 400, 450, 500]
    qr_size = sizes[index % len(sizes)]

    payload = {
        "title": f"StressTest #{index + 1:04d} - {theme['name']} ({dot_type})",
        "type": qr_type,
        "target_url": target_url,
        "design_config": {
            "content": target_url,
            "width": qr_size,
            "height": qr_size,
            "margin": 10,
            "qrOptions": {
                "errorCorrectionLevel": ec_level,
            },
            "dotsOptions": {
                "type": dot_type,
                "color": theme["dots"],
            },
            "cornersSquareOptions": {
                "type": corner_sq_type,
                "color": theme["corner_square"],
            },
            "cornersDotOptions": {
                "type": corner_dot_type,
                "color": theme["corner_dot"],
            },
            "backgroundOptions": {
                "color": theme["bg"],
            },
            "labelTop": {
                "enabled": has_top,
                "text": top_text if has_top else "",
                "fontSize": 14,
                "fontWeight": "bold",
                "color": theme["label"],
                "align": "center",
                "padding": 8,
            },
            "labelBottom": {
                "enabled": has_bottom,
                "text": bottom_text if has_bottom else "",
                "fontSize": 12,
                "fontWeight": "normal",
                "color": theme["label"],
                "align": "center",
                "padding": 8,
            },
        },
    }

    return payload, theme["name"], dot_type


# ---------------------------------------------------------------------------
# Individual Worker Task
# ---------------------------------------------------------------------------
def process_single_qr(
    index: int,
    base_url: str,
    api_key: str,
    qr_type_pref: str,
    should_export: bool,
    export_fmt_pref: str,
    should_poll: bool,
    should_scan: bool,
    rotate_ips: bool,
    delay_s: float,
    poll_timeout_s: float,
    poll_interval_s: float,
    colors_enabled: bool,
) -> QRResult:
    """Creates a single styled QR code, queues Celery export, and measures timings."""
    if delay_s > 0:
        time.sleep(delay_s * index)

    result = QRResult(index=index)
    payload, theme_name, dot_type = generate_qr_payload(index, qr_type_pref)
    result.title = payload["title"]
    result.qr_type = payload["type"]
    result.style_theme = theme_name
    result.dot_type = dot_type

    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json",
    }
    if rotate_ips:
        # Rotate fake client IP to prevent slowapi IP-rate-limiter from dropping stress test batches
        fake_ip = f"198.51.100.{(index % 250) + 1}"
        headers["CF-Connecting-IP"] = fake_ip
        headers["X-Forwarded-For"] = fake_ip

    # 1. Create QR code via API
    endpoint = f"{base_url}/v1/qrcodes"
    status_code, body, latency = make_request(
        endpoint,
        method="POST",
        headers=headers,
        data=payload,
    )

    result.create_status = status_code
    result.create_latency_ms = latency

    if status_code != 201:
        err_msg = body.get("detail", str(body))
        result.create_error = str(err_msg)
        return result

    qr_id = body.get("id")
    result.qr_id = qr_id
    result.short_code = body.get("short_code")

    # 2. Trigger Celery Async Export if requested
    if should_export and qr_id:
        fmt = (
            EXPORT_FORMATS[index % len(EXPORT_FORMATS)]
            if export_fmt_pref == "random"
            else export_fmt_pref
        )
        result.export_format = fmt

        export_url = f"{base_url}/v1/qrcodes/{qr_id}/export/async?format={fmt}"
        exp_status, exp_body, exp_latency = make_request(
            export_url,
            method="POST",
            headers=headers,
        )

        result.export_latency_ms = exp_latency

        if exp_status == 202:
            job_id = exp_body.get("id")
            result.job_id = job_id
            result.export_status = exp_body.get("status", "PENDING")

            # 3. Poll Celery BatchJob until finished
            if should_poll and job_id:
                job_url = f"{base_url}/v1/qrcodes/jobs/{job_id}"
                deadline = time.time() + poll_timeout_s
                poll_start = time.perf_counter()

                while time.time() < deadline:
                    poll_code, poll_body, _ = make_request(job_url, method="GET", headers=headers)
                    if poll_code == 200:
                        cur_status = str(poll_body.get("status", "")).upper()
                        result.export_status = cur_status
                        if cur_status in ("COMPLETED", "FAILED"):
                            result.download_url = poll_body.get("result_url")
                            result.export_latency_ms += (time.perf_counter() - poll_start) * 1000
                            break
                    time.sleep(poll_interval_s)

                if result.export_status not in ("COMPLETED", "FAILED"):
                    result.export_status = "TIMED_OUT"
        else:
            result.export_status = f"ERROR_{exp_status}"
            result.export_error = str(exp_body.get("detail", exp_body))

    # 4. Trigger Scan Analytics Celery task if dynamic QR code
    if should_scan and result.short_code:
        redirect_base = base_url.replace("/api", "")
        scan_url = f"{redirect_base}/r/{result.short_code}"
        scan_headers = {
            "User-Agent": "PointQR-StressTester/1.0",
        }
        if rotate_ips:
            scan_headers["CF-Connecting-IP"] = f"203.0.113.{(index % 250) + 1}"

        sc_code, _, sc_latency = make_request(
            scan_url,
            method="GET",
            headers=scan_headers,
            follow_redirects=False,
        )
        result.scan_status = sc_code
        result.scan_latency_ms = sc_latency

    return result


# ---------------------------------------------------------------------------
# Auto-Login helper
# ---------------------------------------------------------------------------
def auto_login_and_get_api_key(base_url: str, email: str, password: str) -> str:
    """Log in with email and password, retrieve or generate an API key."""
    login_url = f"{base_url}/v1/auth/login"
    login_data = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        login_url,
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            access_token = data.get("access_token")
    except Exception as e:
        raise RuntimeError(f"Login failed for {email}: {e}")

    keys_url = f"{base_url}/v1/apikeys"
    bearer_headers = {"Authorization": f"Bearer {access_token}"}

    # Generate new key to guarantee plaintext is available
    gen_req = urllib.request.Request(keys_url, headers=bearer_headers, method="POST")
    try:
        with urllib.request.urlopen(gen_req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["api_key"]
    except Exception as e:
        raise RuntimeError(f"Failed to generate API key: {e}")


# ---------------------------------------------------------------------------
# Summary Printer
# ---------------------------------------------------------------------------
def print_summary(summary: TestSummary, colors_enabled: bool = True) -> None:
    """Render a clean ASCII report of the stress test results."""
    print()
    print(c("=" * 72, Colors.CYAN, colors_enabled))
    print(c("  POINTQR API & CELERY STRESS TEST RESULTS", Colors.BOLD + Colors.CYAN, colors_enabled))
    print(c("=" * 72, Colors.CYAN, colors_enabled))

    print(f" Total Duration      : {summary.total_duration_s:.2f} s")
    print(f" Requests Dispatched : {summary.total_requested}")
    print(
        f" QR Codes Created    : {c(str(summary.created_success), Colors.GREEN, colors_enabled)} "
        f"({summary.created_success / summary.total_requested * 100:.1f}%)"
    )
    if summary.created_failed > 0:
        print(f" Creation Failures   : {c(str(summary.created_failed), Colors.RED, colors_enabled)}")
    if summary.rate_limited > 0:
        print(
            f" Rate Limited (429)  : {c(str(summary.rate_limited), Colors.YELLOW, colors_enabled)} "
            f"(Hint: Use --rotate-ips to bypass IP rate limits)"
        )

    # Latencies
    create_latencies = [r.create_latency_ms for r in summary.results if r.create_status == 201]
    if create_latencies:
        create_latencies.sort()
        avg_lat = sum(create_latencies) / len(create_latencies)
        p95_lat = create_latencies[int(len(create_latencies) * 0.95)]
        min_lat = create_latencies[0]
        max_lat = create_latencies[-1]
        throughput = summary.created_success / summary.total_duration_s if summary.total_duration_s > 0 else 0
        print(f" API Latency (ms)    : min={min_lat:.1f} | avg={avg_lat:.1f} | p95={p95_lat:.1f} | max={max_lat:.1f}")
        print(f" Creation Throughput : {throughput:.1f} qr/sec")

    # Celery Export Queue Stats
    if summary.export_dispatched > 0:
        print(c("-" * 72, Colors.DIM, colors_enabled))
        print(c("  CELERY EXPORT QUEUE (queue: 'qr_export')", Colors.BOLD + Colors.MAGENTA, colors_enabled))
        print(f" Tasks Dispatched    : {summary.export_dispatched}")
        print(
            f" Tasks Completed     : {c(str(summary.export_completed), Colors.GREEN, colors_enabled)} "
            f"({summary.export_completed / summary.export_dispatched * 100:.1f}%)"
        )
        if summary.export_failed > 0:
            print(f" Tasks Failed/Timeout: {c(str(summary.export_failed), Colors.RED, colors_enabled)}")

        exp_latencies = [
            r.export_latency_ms for r in summary.results if r.export_status == "COMPLETED"
        ]
        if exp_latencies:
            exp_latencies.sort()
            avg_exp = sum(exp_latencies) / len(exp_latencies)
            p95_exp = exp_latencies[int(len(exp_latencies) * 0.95)]
            print(f" Export Duration(ms) : avg={avg_exp:.1f} | p95={p95_exp:.1f} | max={exp_latencies[-1]:.1f}")

    # Scan Analytics Stats
    if summary.scans_dispatched > 0:
        print(c("-" * 72, Colors.DIM, colors_enabled))
        print(c("  CELERY SCAN ANALYTICS QUEUE (queue: 'scan_analytics')", Colors.BOLD + Colors.BLUE, colors_enabled))
        print(f" Scans Dispatched    : {summary.scans_dispatched}")
        print(
            f" Scans Redirected    : {c(str(summary.scans_success), Colors.GREEN, colors_enabled)} "
            f"({summary.scans_success / summary.scans_dispatched * 100:.1f}%)"
        )

    print(c("=" * 72, Colors.CYAN, colors_enabled))


# ---------------------------------------------------------------------------
# Main CLI Entrypoint
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="PointQR API & Celery Queue Stress Testing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test creating 10 styled QR codes and async export tasks:
  python3 scripts/stress_test_qrcodes.py --api-key <KEY> -n 10

  # Heavy stress test with 100 QR codes, 10 concurrent threads, and polling:
  python3 scripts/stress_test_qrcodes.py -k <KEY> -n 100 -c 10 --poll

  # Use auto-login to automatically get/refresh the API key:
  python3 scripts/stress_test_qrcodes.py --auto-login admin@pointqr.dev:BippityBopBoo123! -n 25

  # Dry-run preview of styled payloads:
  python3 scripts/stress_test_qrcodes.py --dry-run -n 5
        """,
    )

    parser.add_argument(
        "-k", "--api-key",
        default=os.environ.get("POINTQR_API_KEY"),
        help="Personal API key for authentication (or env var POINTQR_API_KEY).",
    )
    parser.add_argument(
        "--auto-login",
        metavar="EMAIL:PASSWORD | EMAIL",
        help="Authenticate using credentials and fetch/generate an API key automatically. "
             "Wrap in single quotes if password contains '!' (e.g. 'user@domain.com:Pass!123').",
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("POINTQR_EMAIL"),
        help="Login email address for authentication (or env var POINTQR_EMAIL).",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("POINTQR_PASSWORD"),
        help="Login password for authentication (or env var POINTQR_PASSWORD). "
             "If omitted when email is supplied, you will be prompted securely.",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=10,
        help="Total number of QR codes to generate (default: 10).",
    )
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent worker threads (default: 5).",
    )
    parser.add_argument(
        "-u", "--url",
        default="http://localhost/api",
        help="Base API URL without trailing slash (default: http://localhost/api).",
    )
    parser.add_argument(
        "--type",
        choices=["mixed", "static", "dynamic"],
        default="mixed",
        help="QR code type: mixed (alternates static/dynamic), static, or dynamic (default: mixed).",
    )
    parser.add_argument(
        "--export",
        dest="export",
        action="store_true",
        default=True,
        help="Enqueue Celery async export job for each created QR code (default: True).",
    )
    parser.add_argument(
        "--no-export",
        dest="export",
        action="store_false",
        help="Disable Celery async export dispatch.",
    )
    parser.add_argument(
        "--format",
        choices=["random", "png", "svg", "pdf", "eps"],
        default="random",
        help="Export file format for Celery render worker (default: random).",
    )
    parser.add_argument(
        "--poll",
        dest="poll",
        action="store_true",
        default=True,
        help="Poll Celery BatchJob status until completion and report latency (default: True).",
    )
    parser.add_argument(
        "--no-poll",
        dest="poll",
        action="store_false",
        help="Do not poll Celery export jobs (fire-and-forget).",
    )
    parser.add_argument(
        "--simulate-scans",
        action="store_true",
        default=False,
        help="Hit dynamic QR redirect /r/{code} to test Celery 'scan_analytics' worker queue.",
    )
    parser.add_argument(
        "--rotate-ips",
        action="store_true",
        default=True,
        help="Rotate client IP header to bypass slowapi 30 req/min rate limit during stress tests (default: True).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Optional artificial delay between thread starts in seconds (default: 0.0).",
    )
    parser.add_argument(
        "--poll-timeout",
        type=float,
        default=15.0,
        help="Max seconds to wait for a Celery export job to reach COMPLETED (default: 15.0).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Interval between export job status checks in seconds (default: 0.5).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI terminal colors.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print sample styled payloads and exit without sending requests.",
    )

    args = parser.parse_args()
    colors_enabled = not args.no_color and sys.stdout.isatty()

    # Dry run mode
    if args.dry_run:
        print(c("--- DRY RUN: PREVIEWING GENERATED STYLED PAYLOADS ---", Colors.BOLD + Colors.CYAN, colors_enabled))
        for i in range(min(args.count, 5)):
            payload, theme, dot = generate_qr_payload(i, args.type)
            print(f"\n[QR #{i + 1}] Theme: {theme} | Dots: {dot} | Type: {payload['type']}")
            print(json.dumps(payload, indent=2))
        print(c(f"\nDry run complete. Sampled {min(args.count, 5)} styles.", Colors.GREEN, colors_enabled))
        return 0

    # Resolve API Key
    api_key = args.api_key
    email = args.email
    password = args.password

    if not api_key and args.auto_login:
        if ":" in args.auto_login:
            email, password = args.auto_login.split(":", 1)
        else:
            email = args.auto_login

    if not api_key and email:
        if not password:
            import getpass
            try:
                password = getpass.getpass(f"Password for {email}: ")
            except (EOFError, KeyboardInterrupt):
                print()
                return 1

        print(c(f"Authenticating as {email}...", Colors.DIM, colors_enabled))
        try:
            api_key = auto_login_and_get_api_key(args.url.rstrip("/"), email, password)
            print(c(f"Obtained API key: {api_key[:8]}••••••••", Colors.GREEN, colors_enabled))
        except Exception as e:
            print(c(f"Auto-login failed: {e}", Colors.RED, colors_enabled), file=sys.stderr)
            return 1

    if not api_key:
        print(
            c("Error: Missing API key. Pass --api-key <KEY>, set POINTQR_API_KEY, or use --email / --auto-login", Colors.RED, colors_enabled),
            file=sys.stderr,
        )
        return 1

    base_url = args.url.rstrip("/")

    print(c("=" * 72, Colors.CYAN, colors_enabled))
    print(c("  POINTQR API & CELERY STRESS TEST RUNNER", Colors.BOLD + Colors.CYAN, colors_enabled))
    print(c("=" * 72, Colors.CYAN, colors_enabled))
    print(f" Target API       : {base_url}")
    print(f" Total QR Codes   : {c(str(args.count), Colors.BOLD, colors_enabled)}")
    print(f" Concurrency      : {args.concurrency} parallel threads")
    print(f" QR Type Mode     : {args.type}")
    print(f" Celery Export    : {'Enabled (' + args.format + ')' if args.export else 'Disabled'}")
    print(f" Celery Polling   : {'Enabled (timeout ' + str(args.poll_timeout) + 's)' if args.poll else 'Disabled'}")
    print(f" IP Rate Rotation : {'Enabled' if args.rotate_ips else 'Disabled'}")
    print(c("-" * 72, Colors.DIM, colors_enabled))

    summary = TestSummary(total_requested=args.count)
    start_wall = time.perf_counter()

    # Dispatch tasks using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_to_idx = {
            executor.submit(
                process_single_qr,
                i,
                base_url,
                api_key,
                args.type,
                args.export,
                args.format,
                args.poll,
                args.simulate_scans,
                args.rotate_ips,
                args.delay,
                args.poll_timeout,
                args.poll_interval,
                colors_enabled,
            ): i
            for i in range(args.count)
        }

        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            res = future.result()
            summary.results.append(res)
            completed_count += 1

            # Progress tracking line
            if res.create_status == 201:
                summary.created_success += 1
                status_badge = c("CREATE OK", Colors.GREEN, colors_enabled)
                exp_detail = ""
                if res.export_status:
                    summary.export_dispatched += 1
                    if res.export_status == "COMPLETED":
                        summary.export_completed += 1
                        exp_badge = c(f"CELERY {res.export_format.upper()} OK", Colors.MAGENTA, colors_enabled)
                    else:
                        summary.export_failed += 1
                        exp_badge = c(f"CELERY {res.export_status}", Colors.RED, colors_enabled)
                    exp_detail = f" | {exp_badge} ({res.export_latency_ms:.0f}ms)"

                if res.scan_status is not None:
                    summary.scans_dispatched += 1
                    if res.scan_status in (200, 301, 302, 307):
                        summary.scans_success += 1

                print(
                    f"[{completed_count:03d}/{args.count:03d}] {status_badge} ({res.create_latency_ms:.0f}ms) "
                    f"| {res.title[:38]:<38}{exp_detail}"
                )
            elif res.create_status == 429:
                summary.rate_limited += 1
                summary.created_failed += 1
                badge = c("RATE LIMITED (429)", Colors.YELLOW, colors_enabled)
                print(f"[{completed_count:03d}/{args.count:03d}] {badge} | {res.title[:38]}")
            else:
                summary.created_failed += 1
                badge = c(f"FAILED ({res.create_status})", Colors.RED, colors_enabled)
                print(f"[{completed_count:03d}/{args.count:03d}] {badge} | Error: {res.create_error}")

    summary.total_duration_s = time.perf_counter() - start_wall
    print_summary(summary, colors_enabled)

    return 0 if summary.created_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

