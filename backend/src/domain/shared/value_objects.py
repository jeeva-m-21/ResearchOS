"""Shared value objects"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OrganizationId(BaseModel):
    value: UUID

class UserId(BaseModel):
    value: UUID

class ProjectId(BaseModel):
    value: UUID

class Timestamps(BaseModel):
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
