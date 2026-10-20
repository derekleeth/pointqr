"""External integrations for feedback: GitHub Issues & Slack webhook.

Errors are caught and logged rather than re-raised so that a
misconfigured token or webhook never blocks a user-facing request.
"""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# GitHub Issues
# ---------------------------------------------------------------------------

_GITHUB_LABEL_MAP = {
    "bug": "bug",
    "feature_request": "enhancement",
}


async def create_github_issue(
    subject: str,
    message: str,
    feedback_type: str,
    user_email: str,
) -> dict | None:
    """Create an issue on GitHub and return ``{"url": ..., "number": ...}``.

    Returns ``None`` if GitHub integration is not configured or the API call
    fails.  Errors are logged but never raised (fire-and-forget).
    """
    if not settings.github_token or not settings.github_repo:
        logger.debug("GitHub integration not configured; skipping issue creation.")
        return None

    label = _GITHUB_LABEL_MAP.get(feedback_type)
    labels = [label] if label else []

    body = (
        f"**Submitted by:** {user_email}\n"
        f"**Type:** {feedback_type}\n\n"
        f"---\n\n{message}"
    )

    url = f"https://api.github.com/repos/{settings.github_repo}/issues"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "title": f"[{feedback_type.replace('_', ' ').title()}] {subject}",
        "body": body,
        "labels": labels,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "GitHub issue #%s created: %s", data["number"], data["html_url"]
            )
            return {"url": data["html_url"], "number": data["number"]}
    except Exception:  # noqa: BLE001
        logger.exception("Failed to create GitHub issue for: %s", subject)
        return None


# ---------------------------------------------------------------------------
# Slack Webhook
# ---------------------------------------------------------------------------

_TYPE_EMOJI = {
    "feedback": "💬",
    "question": "❓",
    "bug": "🐛",
    "feature_request": "💡",
}


async def send_slack_notification(
    subject: str,
    message: str,
    feedback_type: str,
    user_email: str,
    github_issue_url: str | None = None,
) -> bool:
    """Send a message to Slack via incoming webhook.

    Returns ``True`` on success, ``False`` otherwise.
    Errors are logged but never raised.
    """
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook not configured; skipping notification.")
        return False

    emoji = _TYPE_EMOJI.get(feedback_type, "📝")
    text = (
        f"{emoji} *New {feedback_type.replace('_', ' ').title()}*\n"
        f"*From:* {user_email}\n"
        f"*Subject:* {subject}\n"
    )
    if github_issue_url:
        text += f"*GitHub:* <{github_issue_url}|View issue>\n"
    text += f"\n>>> {message[:1500]}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                settings.slack_webhook_url,
                json={"text": text},
            )
            resp.raise_for_status()
            logger.info("Slack notification sent for feedback: %s", subject)
            return True
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send Slack notification for: %s", subject)
        return False

