"""Local filesystem storage adapter for artifacts."""
import hashlib
import os
from pathlib import Path
from typing import Optional
from uuid import UUID


class LocalStorage:
    """Store artifact files on the local filesystem.

    Files are organized as::

        {base_dir}/{org_id}/{artifact_id}/{version}/{filename}

    The base directory is configured via the ``ARTIFACT_STORAGE_DIR``
    environment variable (default ``./data/artifacts``).
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.getenv("ARTIFACT_STORAGE_DIR", "./data/artifacts")
        self.base_dir = Path(base_dir)

    def _resolve(self, *parts: str) -> Path:
        """Resolve a path relative to the base directory, ensuring it is
        contained within the base directory (path traversal guard)."""
        full = self.base_dir.joinpath(*parts).resolve()
        if not str(full).startswith(str(self.base_dir.resolve())):
            raise ValueError("Path traversal detected")
        return full

    async def save(
        self,
        organization_id: UUID,
        artifact_id: UUID,
        version: int,
        filename: str,
        data: bytes,
    ) -> str:
        """Save a file and return the relative storage path.

        The returned path is relative to the base directory so it can be
        stored in the database and later used to read the file.
        """
        rel = Path(str(organization_id)) / str(artifact_id) / str(version) / filename
        full = self._resolve(str(rel))
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        return str(rel)

    async def read(self, storage_path: str) -> bytes:
        """Read a file by its relative storage path."""
        full = self._resolve(storage_path)
        return full.read_bytes()

    async def delete(self, storage_path: str) -> None:
        """Delete a file by its relative storage path."""
        full = self._resolve(storage_path)
        if full.exists():
            full.unlink()

    def compute_hash(self, data: bytes) -> str:
        """Compute the SHA-256 hash of data."""
        return hashlib.sha256(data).hexdigest()
