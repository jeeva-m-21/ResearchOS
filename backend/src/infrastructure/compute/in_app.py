"""In-app compute provider — runs code in a subprocess sandbox."""
import asyncio
import time
from typing import Optional
from uuid import uuid4

from src.application.compute.dto import ExecutionRequest, ExecutionResult
from src.application.compute.provider import ComputeProvider
from src.infrastructure.database import Database

# Default global db instance
from src.infrastructure.database import db as _default_db


class InAppProvider(ComputeProvider):
    """Execute notebook blocks via subprocess (existing in-app executor).

    Supports Python execution in a subprocess sandbox.
    Rust and SQL return a "not yet supported" message.

    Args:
        db: Database instance for persisting execution records.
            Defaults to the global ``src.infrastructure.database.db``.
    """

    # Timeout per block type (ms)
    _BLOCK_TIMEOUTS = {
        "python": 30_000,
        "rust": 60_000,
        "sql": 15_000,
    }

    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db or _default_db

    @property
    def name(self) -> str:
        return "in_app"

    @staticmethod
    async def _run_python(code: str, timeout_ms: int) -> tuple[int, str, str]:
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

    async def health(self) -> bool:
        """Check if Python3 is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(), timeout=5
            )
            return proc.returncode == 0 and "Python" in (stdout.decode() or "")
        except Exception:
            return False

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute a block in-process via subprocess.

        Stores execution records in the database and returns the result.
        """
        timeout_ms = request.timeout_ms or self._BLOCK_TIMEOUTS.get(
            request.block_type, 30_000
        )

        execution_id = uuid4()
        started_at = time.time()

        # Persist execution record if DB is connected
        if self._db.pool is not None:
            await self._db.execute(
                """
                INSERT INTO executions
                    (id, block_content_id, block_id, notebook_id, organization_id,
                     status, created_by)
                VALUES ($1, $2, $3, $4, $5, 'running', $6)
                """,
                execution_id,
                request.block_content_id,
                request.block_id,
                request.notebook_id,
                request.organization_id,
                request.created_by,
            )

        try:
            if request.block_type == "python":
                returncode, stdout, stderr = await self._run_python(
                    request.content, timeout_ms
                )
            elif request.block_type == "rust":
                returncode, stdout, stderr = (
                    -1,
                    "",
                    "Rust execution not yet supported",
                )
            elif request.block_type == "sql":
                returncode, stdout, stderr = (
                    -1,
                    "",
                    "SQL execution not yet supported",
                )
            else:
                msg = f"Block type '{request.block_type}' does not support execution"
                returncode, stdout, stderr = 0, "", msg

            ended_at = time.time()
            duration_ms = int((ended_at - started_at) * 1000)
            status = "success" if returncode == 0 else "failed"
            output = stdout if stdout else None
            error = stderr if stderr else None

            if self._db.pool is not None:
                await self._db.execute(
                    """
                    UPDATE executions
                    SET status = $1, ended_at = NOW(), duration_ms = $2,
                        output = $3, error = $4
                    WHERE id = $5
                    """,
                    status,
                    duration_ms,
                    output,
                    error,
                    execution_id,
                )

            return ExecutionResult(
                execution_id=execution_id,
                status=status,
                output=output,
                error=error,
                duration_ms=duration_ms,
                provider=self.name,
            )

        except Exception as exc:
            ended_at = time.time()
            duration_ms = int((ended_at - started_at) * 1000)

            if self._db.pool is not None:
                await self._db.execute(
                    """
                    UPDATE executions
                    SET status = 'failed', ended_at = NOW(),
                        duration_ms = $1, error = $2
                    WHERE id = $3
                    """,
                    duration_ms,
                    str(exc),
                    execution_id,
                )

            return ExecutionResult(
                execution_id=execution_id,
                status="failed",
                output=None,
                error=str(exc),
                duration_ms=duration_ms,
                provider=self.name,
            )
