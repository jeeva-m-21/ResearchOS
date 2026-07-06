"""Compute DTOs — request/result models for block execution."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """Request to execute a block on a compute provider."""

    block_id: UUID
    notebook_id: UUID
    block_content_id: UUID
    block_type: str = Field(
        description="Type of block to execute (python, rust, sql)"
    )
    content: str = Field(description="Code/content to execute")
    organization_id: UUID
    created_by: UUID
    timeout_ms: int = Field(default=30_000, ge=100, le=300_000)
    provider: str = Field(
        default="in_app",
        description="Compute provider to use (in_app, local_jupyter, cloud_gcp)",
    )


class ExecutionResult(BaseModel):
    """Result of executing a block on a compute provider."""

    execution_id: UUID
    status: str = Field(
        description="Execution status: success, failed, timeout"
    )
    output: Optional[str] = Field(
        default=None, description="Standard output from execution"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )
    duration_ms: Optional[int] = Field(
        default=None, description="Execution duration in milliseconds"
    )
    provider: str = Field(
        default="in_app", description="Compute provider used"
    )
