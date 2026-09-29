"""Pydantic schemas for BatchJob API responses."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.batch_job import BatchJobStatus


class BatchJobRead(BaseModel):
    """Read schema for a BatchJob returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: BatchJobStatus
    total_items: int
    processed_items: int
    result_url: Optional[str]
    created_at: datetime
