"""File hashing utilities for artifact integrity verification."""

import hashlib
from pathlib import Path
from typing import Union

_CHUNK_SIZE = 64 * 1024  # 64 KB


def sha256_file(path: Union[str, Path]) -> str:
    """Compute SHA-256 hex digest of a file.

    Reads the file in chunks to handle large files efficiently.

    Args:
        path: Path to the file.

    Returns:
        Hex-encoded SHA-256 digest string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hex digest of a byte string."""
    return hashlib.sha256(data).hexdigest()
