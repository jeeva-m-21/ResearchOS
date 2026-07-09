"""Artifact endpoints"""
import os
from typing import Any, Optional
from uuid import UUID, uuid4

from api.dependencies.auth import (
    get_current_org_with_membership,
    get_current_user,
)
from api.dependencies.events import get_event_producer
from domain.artifacts.entities import ArtifactType
from domain.artifacts.events import ArtifactUploaded
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from infrastructure.adapters.storage import LocalStorage
from infrastructure.auth.jwt import TokenData
from infrastructure.database import db
from infrastructure.events.producer import EventProducer

router = APIRouter()

# Allowed MIME types for artifact uploads (basic validation)
ALLOWED_MIME_PREFIXES = (
    "image/", "text/", "application/json", "application/pdf",
    "application/octet-stream", "application/xml", "application/zip",
    "application/x-tar", "application/gzip",
)


def _is_mime_allowed(mime: str) -> bool:
    return any(mime.startswith(p) for p in ALLOWED_MIME_PREFIXES)


@router.post("/upload")
async def upload_artifact(
    file: UploadFile,
    artifact_type: str = Query(
        default="text",
        description="Type of artifact (model, dataset, image, etc.)",
    ),
    experiment_id: Optional[UUID] = Query(default=None),
    run_id: Optional[UUID] = Query(default=None),
    notebook_id: Optional[UUID] = Query(default=None),
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
    event_producer: EventProducer = Depends(get_event_producer),
) -> dict[str, Any]:
    """Upload an artifact file."""
    # Validate artifact type
    valid_types = {t.value for t in ArtifactType}
    if artifact_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid artifact_type '{artifact_type}'. "
                f"Valid types: {sorted(valid_types)}"
            ),
        )

    # Read file data
    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Determine MIME type
    mime_type = file.content_type or "application/octet-stream"
    filename = file.filename or "unnamed"

    # Init storage adapter
    storage = LocalStorage()

    # Compute hash
    hash_sha256 = storage.compute_hash(data)

    # Generate IDs
    artifact_id = uuid4()
    version = 1

    # Save to local filesystem
    storage_path = await storage.save(
        organization_id=organization_id,
        artifact_id=artifact_id,
        version=version,
        filename=filename,
        data=data,
    )

    # Insert artifact record
    await db.execute(
        """
        INSERT INTO artifacts (
            id, organization_id, name, artifact_type, mime_type,
            size_bytes, hash_sha256, current_version,
            experiment_id, run_id, notebook_id, created_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """,
        artifact_id, organization_id, filename, artifact_type,
        mime_type, len(data), hash_sha256, version,
        experiment_id, run_id, notebook_id, user.user_id,
    )

    # Insert version record
    await db.execute(
        """
        INSERT INTO artifact_versions (
            id, artifact_id, organization_id, version,
            storage_path, size_bytes, hash_sha256, created_by
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        uuid4(), artifact_id, organization_id, version,
        storage_path, len(data), hash_sha256, user.user_id,
    )

    # Emit event
    event = ArtifactUploaded(
        aggregate_id=artifact_id,
        artifact_id=artifact_id,
        organization_id=organization_id,
        name=filename,
        artifact_type=artifact_type,
        mime_type=mime_type,
        size_bytes=len(data),
        hash_sha256=hash_sha256,
        experiment_id=experiment_id,
        run_id=run_id,
    )
    await event_producer.emit(event)

    return {
        "id": str(artifact_id),
        "name": filename,
        "artifact_type": artifact_type,
        "mime_type": mime_type,
        "size_bytes": len(data),
        "hash_sha256": hash_sha256,
        "version": version,
    }


@router.get("/")
async def list_artifacts(
    experiment_id: Optional[UUID] = Query(default=None),
    run_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> list[dict[str, Any]]:
    """List artifacts for the organization."""
    if experiment_id:
        rows = await db.fetch_all(
            """
            SELECT id, name, artifact_type, mime_type, size_bytes,
                   hash_sha256, current_version, created_at
            FROM artifacts
            WHERE organization_id = $1
            AND experiment_id = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            organization_id, experiment_id, limit, offset,
        )
    elif run_id:
        rows = await db.fetch_all(
            """
            SELECT id, name, artifact_type, mime_type, size_bytes,
                   hash_sha256, current_version, created_at
            FROM artifacts
            WHERE organization_id = $1
            AND run_id = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            organization_id, run_id, limit, offset,
        )
    else:
        rows = await db.fetch_all(
            """
            SELECT id, name, artifact_type, mime_type, size_bytes,
                   hash_sha256, current_version, created_at
            FROM artifacts
            WHERE organization_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            organization_id, limit, offset,
        )

    return [dict(r) for r in rows]


@router.get("/{artifact_id}")
async def get_artifact(
    artifact_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> dict[str, Any]:
    """Get artifact metadata by ID."""
    row = await db.fetch_one(
        """
        SELECT id, name, artifact_type, mime_type, size_bytes,
               hash_sha256, current_version, experiment_id, run_id,
               notebook_id, created_at
        FROM artifacts
        WHERE id = $1 AND organization_id = $2
        """,
        artifact_id, organization_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    return dict(row)


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: UUID,
    user: TokenData = Depends(get_current_user),
    organization_id: UUID = Depends(get_current_org_with_membership),
) -> FileResponse:
    """Download the latest version of an artifact file."""
    row = await db.fetch_one(
        """
        SELECT a.name, a.mime_type, a.current_version,
               av.storage_path
        FROM artifacts a
        JOIN artifact_versions av
            ON av.artifact_id = a.id
            AND av.version = a.current_version
        WHERE a.id = $1 AND a.organization_id = $2
        """,
        artifact_id, organization_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )

    base_dir = os.getenv("ARTIFACT_STORAGE_DIR", "./data/artifacts")
    file_path = os.path.join(base_dir, row["storage_path"])

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact file not found on storage",
        )

    return FileResponse(
        path=file_path,
        media_type=row["mime_type"],
        filename=row["name"],
    )
