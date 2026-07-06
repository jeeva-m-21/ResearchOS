"""Block executor service — runs notebook blocks in a subprocess sandbox."""
import asyncio
import time
from typing import Any, Optional
from uuid import UUID, uuid4

from src.infrastructure.database import db

# Timeout per block type (ms)
BLOCK_TIMEOUTS = {
    "python": 30_000,
    "rust": 60_000,
    "sql": 15_000,
}


async def _run_python(code: str, timeout_ms: int) -> tuple[int, str, Optional[str]]:
    """Run Python code in a subprocess. Returns (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        "python3", "-c", code,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_ms / 1000
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return -1, "", "Execution timed out"

    out = stdout.decode() if stdout else ""
    err = stderr.decode() if stderr else ""
    return proc.returncode or 0, out, err


async def execute_block(
    block_id: UUID,
    notebook_id: UUID,
    block_content_id: UUID,
    block_type: str,
    content: str,
    organization_id: UUID,
    created_by: UUID,
) -> dict[str, Any]:
    """
    Execute a notebook block.

    Args:
        block_id: The block ID
        notebook_id: The notebook ID
        block_content_id: The specific content version to execute
        block_type: Type of block (python, rust, sql)
        content: The code/content to execute
        organization_id: Tenant ID
        created_by: User ID executing the block

    Returns:
        Result dict with execution_id, status, output, error, duration_ms
    """
    timeout_ms = BLOCK_TIMEOUTS.get(block_type, 30_000)

    # Insert execution record with status=running
    execution_id = uuid4()
    started_at = time.time()

    await db.execute(
        """
        INSERT INTO executions
            (id, block_content_id, block_id, notebook_id, organization_id,
             status, created_by)
        VALUES ($1, $2, $3, $4, $5, 'running', $6)
        """,
        execution_id, block_content_id, block_id, notebook_id,
        organization_id, created_by,
    )

    try:
        if block_type == "python":
            returncode, stdout, stderr = await _run_python(content, timeout_ms)
        elif block_type == "rust":
            # Placeholder for Rust execution
            returncode, stdout, stderr = -1, "", "Rust execution not yet supported"
        elif block_type == "sql":
            # Placeholder for SQL execution
            returncode, stdout, stderr = -1, "", "SQL execution not yet supported"
        else:
            msg = f"Block type '{block_type}' does not support execution"
            returncode, stdout, stderr = 0, "", msg

        ended_at = time.time()
        duration_ms = int((ended_at - started_at) * 1000)
        status = "success" if returncode == 0 else "failed"
        output = stdout if stdout else None
        error = stderr if stderr else None

        await db.execute(
            """
            UPDATE executions
            SET status = $1, ended_at = NOW(), duration_ms = $2,
                output = $3, error = $4
            WHERE id = $5
            """,
            status, duration_ms, output, error, execution_id,
        )

        return {
            "execution_id": str(execution_id),
            "status": status,
            "output": output,
            "error": error,
            "duration_ms": duration_ms,
        }

    except Exception as exc:
        ended_at = time.time()
        duration_ms = int((ended_at - started_at) * 1000)

        await db.execute(
            """
            UPDATE executions
            SET status = 'failed', ended_at = NOW(), duration_ms = $1, error = $2
            WHERE id = $3
            """,
            duration_ms, str(exc), execution_id,
        )

        return {
            "execution_id": str(execution_id),
            "status": "failed",
            "output": None,
            "error": str(exc),
            "duration_ms": duration_ms,
        }
