"""Settings API routes — API keys, connection configs, provider settings"""
import json
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies.auth import get_current_org_with_membership, get_current_user
from infrastructure.auth.jwt import TokenData
from infrastructure.database import db

router = APIRouter(tags=["Settings"])


# ─── Schemas ──────────────────────────────────────────────────────────────

class ConnectionConfig(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    provider: str
    config: dict[str, object]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectionCreate(BaseModel):
    name: str
    provider: str
    config: dict[str, object] = {}
    is_active: bool = False


class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict[str, object]] = None
    is_active: Optional[bool] = None


class APIKeyInfo(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


# ─── Connections ───────────────────────────────────────────────────────────

@router.get("/v1/settings/connections", response_model=list[ConnectionConfig])
async def list_connections(
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """List all connection configs for the organization"""
    rows = await db.fetch_all(
        """SELECT id, organization_id, name, provider, config,
                  is_active, created_at, updated_at
           FROM connection_configs
           WHERE organization_id = $1 AND deleted_at IS NULL
           ORDER BY created_at DESC""",
        organization_id,
    )
    return [dict(r) for r in rows]


@router.post(
    "/v1/settings/connections", response_model=ConnectionConfig, status_code=201
)
async def create_connection(
    request: ConnectionCreate,
    organization_id: UUID = Depends(get_current_org_with_membership),
    token_data: TokenData = Depends(get_current_user),
):
    """Create a new connection config"""
    conn_id = uuid4()
    now = datetime.utcnow()
    await db.execute(
        """INSERT INTO connection_configs
           (id, organization_id, name, provider, config,
            is_active, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)""",
        conn_id,
        organization_id,
        request.name,
        request.provider,
        json.dumps(request.config),
        request.is_active,
        now,
        now,
    )
    return ConnectionConfig(
        id=conn_id,
        organization_id=organization_id,
        name=request.name,
        provider=request.provider,
        config=request.config,
        is_active=request.is_active,
        created_at=now,
        updated_at=now,
    )


@router.put("/v1/settings/connections/{connection_id}", response_model=ConnectionConfig)
async def update_connection(
    connection_id: UUID,
    request: ConnectionUpdate,
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Update a connection config"""
    sets: list[str] = []
    params: list[object] = [connection_id, organization_id]
    idx = 3

    if request.name is not None:
        sets.append(f"name = ${idx}")
        params.append(request.name)
        idx += 1
    if request.config is not None:
        sets.append(f"config = ${idx}::jsonb")
        params.append(json.dumps(request.config))
        idx += 1
    if request.is_active is not None:
        sets.append(f"is_active = ${idx}")
        params.append(request.is_active)
        idx += 1

    sets.append(f"updated_at = ${idx}")
    params.append(datetime.utcnow())

    await db.execute(
        "UPDATE connection_configs"
        f" SET {', '.join(sets)}"
        " WHERE id = $1 AND organization_id = $2 AND deleted_at IS NULL",
        *params,
    )

    row = await db.fetch_one(
        "SELECT * FROM connection_configs WHERE id = $1 AND organization_id = $2",
        connection_id,
        organization_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Connection not found")
    return dict(row)


@router.delete("/v1/settings/connections/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: UUID,
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Soft-delete a connection config"""
    await db.execute(
        "UPDATE connection_configs"
        " SET deleted_at = NOW()"
        " WHERE id = $1 AND organization_id = $2",
        connection_id,
        organization_id,
    )


# ─── API Keys ──────────────────────────────────────────────────────────────

@router.get("/v1/settings/api-keys", response_model=list[APIKeyInfo])
async def list_api_keys(
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """List API keys for the organization (without the actual key hashes)"""
    rows = await db.fetch_all(
        """SELECT id, name, created_at, last_used_at, expires_at
           FROM api_keys
           WHERE organization_id = $1 AND deleted_at IS NULL
           ORDER BY created_at DESC""",
        organization_id,
    )
    return [dict(r) for r in rows]


@router.delete("/v1/settings/api-keys/{key_id}", status_code=204)
async def delete_api_key(
    key_id: UUID,
    organization_id: UUID = Depends(get_current_org_with_membership),
):
    """Revoke (soft-delete) an API key"""
    await db.execute(
        "UPDATE api_keys SET deleted_at = NOW() WHERE id = $1 AND organization_id = $2",
        key_id,
        organization_id,
    )


# ─── Status ────────────────────────────────────────────────────────────────

@router.get("/v1/settings/status")
async def get_settings_status():
    """Health check for settings module"""
    return {"status": "ok"}
