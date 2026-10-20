"""Feedback submission endpoints: user-facing + admin management."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.core.dependencies import AdminUser, CurrentUser, DBSession
from app.core.rate_limit import limiter
from app.models.feedback import FeedbackSubmission, FeedbackType
from app.schemas.feedback import (
    FeedbackAdminRead,
    FeedbackCreate,
    FeedbackRead,
    FeedbackStatusUpdate,
)
from app.services.feedback import create_github_issue, send_slack_notification

router = APIRouter(prefix="/feedback", tags=["feedback"])


# ---------------------------------------------------------------------------
# POST /feedback – submit feedback (authenticated users)
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback, bug report, or feature request",
)
@limiter.limit("5/minute")
async def submit_feedback(
    request: Request,  # required by slowapi
    payload: FeedbackCreate,
    user: CurrentUser,
    db: DBSession,
) -> FeedbackSubmission:
    """Create a feedback submission. Automatically routes to GitHub or Slack."""
    submission = FeedbackSubmission(
        user_id=user.id,
        type=payload.type,
        subject=payload.subject,
        message=payload.message,
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    # Route to external services (fire-and-forget — failures don't block)
    if payload.type in (FeedbackType.bug, FeedbackType.feature_request):
        result = await create_github_issue(
            subject=payload.subject,
            message=payload.message,
            feedback_type=payload.type.value,
            user_email=user.email,
        )
        if result:
            submission.github_issue_url = result["url"]
            submission.github_issue_number = result["number"]
            await db.flush()
            await db.refresh(submission)

    # Always notify Slack; include the GitHub issue link when one was created
    sent = await send_slack_notification(
        subject=payload.subject,
        message=payload.message,
        feedback_type=payload.type.value,
        user_email=user.email,
        github_issue_url=submission.github_issue_url,
    )
    if sent:
        submission.slack_notified = True
        await db.flush()
        await db.refresh(submission)

    return submission


# ---------------------------------------------------------------------------
# GET /feedback – list own submissions (authenticated users)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[FeedbackRead],
    summary="List your feedback submissions",
)
async def list_own_feedback(
    user: CurrentUser,
    db: DBSession,
) -> list[FeedbackSubmission]:
    """Return all feedback submitted by the current user."""
    result = await db.execute(
        select(FeedbackSubmission)
        .where(FeedbackSubmission.user_id == user.id)
        .order_by(FeedbackSubmission.created_at.desc())
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/admin",
    response_model=list[FeedbackAdminRead],
    summary="List all feedback submissions (admin)",
)
async def admin_list_feedback(
    _admin: AdminUser,
    db: DBSession,
) -> list[dict]:
    """Return all feedback with user email for admin review."""
    result = await db.execute(
        select(FeedbackSubmission).order_by(
            FeedbackSubmission.created_at.desc()
        )
    )
    submissions = list(result.scalars().all())
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "user_email": s.user.email,
            "type": s.type.value,
            "subject": s.subject,
            "message": s.message,
            "status": s.status.value,
            "github_issue_url": s.github_issue_url,
            "github_issue_number": s.github_issue_number,
            "slack_notified": s.slack_notified,
            "admin_notes": s.admin_notes,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in submissions
    ]


@router.patch(
    "/admin/{feedback_id}",
    response_model=FeedbackAdminRead,
    summary="Update feedback status (admin)",
)
async def admin_update_feedback(
    feedback_id: uuid.UUID,
    payload: FeedbackStatusUpdate,
    _admin: AdminUser,
    db: DBSession,
) -> dict:
    """Update the status and/or admin notes on a feedback submission."""
    result = await db.execute(
        select(FeedbackSubmission).where(
            FeedbackSubmission.id == feedback_id
        )
    )
    submission = result.scalar_one_or_none()
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback submission not found",
        )

    submission.status = payload.status
    if payload.admin_notes is not None:
        submission.admin_notes = payload.admin_notes
    await db.flush()
    await db.refresh(submission)

    return {
        "id": submission.id,
        "user_id": submission.user_id,
        "user_email": submission.user.email,
        "type": submission.type.value,
        "subject": submission.subject,
        "message": submission.message,
        "status": submission.status.value,
        "github_issue_url": submission.github_issue_url,
        "github_issue_number": submission.github_issue_number,
        "slack_notified": submission.slack_notified,
        "admin_notes": submission.admin_notes,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at,
    }


@router.delete(
    "/admin/{feedback_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a feedback submission (admin)",
)
async def admin_delete_feedback(
    feedback_id: uuid.UUID,
    _admin: AdminUser,
    db: DBSession,
) -> None:
    """Permanently delete a feedback submission."""
    result = await db.execute(
        select(FeedbackSubmission).where(
            FeedbackSubmission.id == feedback_id
        )
    )
    submission = result.scalar_one_or_none()
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback submission not found",
        )
    await db.delete(submission)
    await db.flush()

