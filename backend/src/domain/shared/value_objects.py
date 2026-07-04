"""Shared value objects"""
from uuid import UUID
from datetime import datetime
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
