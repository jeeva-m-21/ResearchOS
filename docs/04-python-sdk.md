# ResearchOS - Python SDK Design

## Overview

The ResearchOS Python SDK provides a crash-safe, offline-first client for logging experiments, metrics, and artifacts with automatic synchronization to the ResearchOS backend.

---

## Design Goals

1. **2-Line API**: Minimal setup to start logging
2. **Crash-Safe**: No data loss on process crash
3. **Offline-First**: Queue events locally, sync when online
4. **Exactly-Once**: No duplicate events
5. **Auto-Logging**: Automatic metric capture (system, GPU)
6. **Backpressure**: Handle slow network gracefully

---

## Quick Start

```python
import researchos as ros

# Initialize (1 line)
ros.init("my-experiment", project="my-project")

# Log metrics (1 line)
ros.log_metric("accuracy", 0.95, step=1)

# Done (automatic flush on exit)
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        USER CODE                                    │
│  ros.init("exp") → ros.log_metric("acc", 0.9) → ros.log_artifact()│
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                      SDK CORE (sync)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Experiment  │  │   Metric     │  │   Artifact   │            │
│  │   Context    │  │   Buffer     │  │   Manager    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                       WAL LAYER (async)                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Write-Ahead Log (JSONL)                                     │ │
│  │  ~/.researchos/events/{org}/{project}/{exp_id}.jsonl        │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  - Append-only file                                               │
│  - One event per line                                             │
│  - Flush on every write (fsync)                                   │
│  - Client-generated event_id (UUID)                              │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                    SYNC ENGINE (background thread)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Event      │  │   Network    │  │   Retry      │            │
│  │   Reader     │  │   Client     │  │   Queue      │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                    │
│  1. Read WAL events (last_sync_offset)                           │
│  2. Batch send to /v1/events/batch                               │
│  3. Ack → update offset                                           │
│  4. Retry on failure (exponential backoff)                       │
│  5. DLQ for permanent failures                                    │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                    BACKEND API (/v1/events/batch)                 │
│  - Deduplicate by event_id                                        │
│  - Append to event store                                          │
│  - Return success                                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
sdk/python/
├── researchos/
│   ├── __init__.py              # Public API
│   ├── client.py                # Main client
│   ├── experiment.py            # Experiment context
│   ├── wal.py                   # Write-ahead log
│   ├── sync.py                  # Sync engine
│   ├── artifact.py              # Artifact uploader
│   ├── autolog/                 # Auto-logging integrations
│   │   ├── __init__.py
│   │   ├── system.py            # CPU, memory, disk
│   │   ├── gpu.py               # NVIDIA GPU metrics
│   │   ├── pytorch.py           # PyTorch hooks
│   │   └── tensorflow.py        # TensorFlow hooks
│   ├── protocol/                # Event protocol
│   │   ├── __init__.py
│   │   ├── events.py            # Event definitions
│   │   └── validation.py        # Schema validation
│   └── utils/
│       ├── __init__.py
│       ├── backoff.py           # Exponential backoff
│       └── hash.py              # File hashing
├── tests/
│   ├── test_wal.py
│   ├── test_sync.py
│   └── test_integration.py
├── pyproject.toml
└── README.md
```

---

## Event Protocol

### Event Types

```python
# researchos/protocol/events.py

from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Any, Literal
from enum import Enum

class EventType(str, Enum):
    EXPERIMENT_STARTED = "experiment.started"
    RUN_STARTED = "run.started"
    METRIC_LOGGED = "metric.logged"
    ARTIFACT_UPLOADED = "artifact.uploaded"
    PARAMETER_SET = "parameter.set"
    RUN_COMPLETED = "run.completed"
    GIT_COMMIT = "git.commit"
    NOTEBOOK_UPDATED = "notebook.updated"
    PAPER_EDITED = "paper.edited"

class BaseEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    organization_id: UUID
    project_id: UUID
    experiment_id: UUID
    run_id: Optional[UUID] = None
    
    class Config:
        use_enum_values = True

class MetricLoggedEvent(BaseEvent):
    event_type: Literal["metric.logged"] = "metric.logged"
    key: str = Field(min_length=1, max_length=255)
    value: float
    step: int = Field(ge=0)
    wall_time: float  # Unix timestamp
    metadata: dict[str, Any] = Field(default_factory=dict)

class ParameterSetEvent(BaseEvent):
    event_type: Literal["parameter.set"] = "parameter.set"
    key: str
    value: str
    value_type: Literal["string", "int", "float", "bool", "json"]

class ArtifactUploadedEvent(BaseEvent):
    event_type: Literal["artifact.uploaded"] = "artifact.uploaded"
    artifact_id: UUID
    name: str
    artifact_type: str  # "model", "dataset", "image", "log"
    mime_type: str
    size_bytes: int
    hash_sha256: str
    storage_path: Optional[str] = None  # Filled after upload

class GitCommitEvent(BaseEvent):
    event_type: Literal["git.commit"] = "git.commit"
    commit_sha: str = Field(min_length=40, max_length=40)
    branch: Optional[str]
    message: Optional[str]
    author: Optional[str]
    is_dirty: bool
    remote_url: Optional[str]

class RunStartedEvent(BaseEvent):
    event_type: Literal["run.started"] = "run.started"
    run_number: int
    git_commit: Optional[str]
    parameters: dict[str, Any]

class RunCompletedEvent(BaseEvent):
    event_type: Literal["run.completed"] = "run.completed"
    status: Literal["completed", "failed", "cancelled"]
    error: Optional[str]
    duration_ms: Optional[int]

class ExperimentStartedEvent(BaseEvent):
    event_type: Literal["experiment.started"] = "experiment.started"
    name: str
    description: Optional[str]
    tags: list[str]

class NotebookUpdatedEvent(BaseEvent):
    event_type: Literal["notebook.updated"] = "notebook.updated"
    notebook_id: UUID
    operation: str  # "add_block", "remove_block", "update_block"
    block_id: Optional[UUID]
    content: Optional[str]

class PaperEditedEvent(BaseEvent):
    event_type: Literal["paper.edited"] = "paper.edited"
    paper_id: UUID
    version: int
    changes: dict[str, Any]
```

### Event Serialization

```python
# researchos/protocol/validation.py

import json
from uuid import UUID

def serialize_event(event: BaseEvent) -> str:
    """Serialize event to JSONL line"""
    return event.model_dump_json()

def deserialize_event(line: str) -> BaseEvent:
    """Deserialize JSONL line to event"""
    data = json.loads(line)
    event_type = data.get("event_type")
    
    event_classes = {
        "metric.logged": MetricLoggedEvent,
        "parameter.set": ParameterSetEvent,
        "artifact.uploaded": ArtifactUploadedEvent,
        "git.commit": GitCommitEvent,
        "run.started": RunStartedEvent,
        "run.completed": RunCompletedEvent,
        "experiment.started": ExperimentStartedEvent,
        "notebook.updated": NotebookUpdatedEvent,
        "paper.edited": PaperEditedEvent,
    }
    
    event_class = event_classes.get(event_type)
    if not event_class:
        raise ValueError(f"Unknown event type: {event_type}")
    
    return event_class(**data)
```

---

## Write-Ahead Log (WAL)

```python
# researchos/wal.py

import os
import json
import fcntl
from pathlib import Path
from uuid import UUID
from typing import Optional
from datetime import datetime

class WAL:
    """
    Write-Ahead Log for crash-safe event persistence.
    
    File format: JSONL (one event per line)
    Location: ~/.researchos/events/{org_id}/{project_id}/{experiment_id}.jsonl
    
    Features:
    - Append-only
    - Fsync on every write
    - File locking for multi-process safety
    - Offset tracking for incremental sync
    """
    
    def __init__(self, base_dir: Path, organization_id: UUID, project_id: UUID, experiment_id: UUID):
        self.base_dir = base_dir
        self.organization_id = organization_id
        self.project_id = project_id
        self.experiment_id = experiment_id
        
        self.file_path = (
            base_dir / 
            "events" / 
            str(organization_id) / 
            str(project_id) / 
            f"{experiment_id}.jsonl"
        )
        self.offset_path = self.file_path.with_suffix(".offset")
        self.lock_path = self.file_path.with_suffix(".lock")
        
        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open file for appending
        self.file = open(self.file_path, "a")
        self.lock_file = open(self.lock_path, "w")
    
    def append(self, event: BaseEvent) -> int:
        """
        Append event to WAL.
        
        Returns:
            Offset (byte position) of written event
        """
        # Acquire exclusive lock
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        
        try:
            # Get current offset
            offset = self.file.tell()
            
            # Serialize event
            line = event.model_dump_json() + "\n"
            
            # Write and sync
            self.file.write(line)
            self.file.flush()
            os.fsync(self.file.fileno())
            
            return offset
        finally:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
    
    def read(self, start_offset: int = 0, batch_size: int = 100) -> list[tuple[int, BaseEvent]]:
        """
        Read events starting from offset.
        
        Returns:
            List of (offset, event) tuples
        """
        events = []
        
        with open(self.file_path, "r") as f:
            f.seek(start_offset)
            
            for _ in range(batch_size):
                line = f.readline()
                if not line:
                    break
                
                offset = f.tell() - len(line)
                event = deserialize_event(line.strip())
                events.append((offset, event))
        
        return events
    
    def get_sync_offset(self) -> int:
        """Get last synced offset"""
        if self.offset_path.exists():
            return int(self.offset_path.read_text().strip())
        return 0
    
    def update_sync_offset(self, offset: int) -> None:
        """Update last synced offset"""
        self.offset_path.write_text(str(offset))
    
    def close(self) -> None:
        """Close WAL file"""
        self.file.close()
        self.lock_file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

---

## Sync Engine

```python
# researchos/sync.py

import asyncio
import time
from typing import Optional
from uuid import UUID
import httpx
from .wal import WAL
from .protocol.events import BaseEvent
from .utils.backoff import ExponentialBackoff

class SyncEngine:
    """
    Background sync engine that pushes events to ResearchOS backend.
    
    Features:
    - Async background thread
    - Batch sending
    - Exponential backoff on failure
    - Dead letter queue for permanent failures
    - Graceful shutdown
    """
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        wal: WAL,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        max_retries: int = 10,
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.wal = wal
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        self.running = False
        self.backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=60.0,
            jitter=True
        )
        
        # Dead letter queue (in-memory, persisted to file)
        self.dlq_path = wal.file_path.with_suffix(".dlq")
    
    async def start(self) -> None:
        """Start sync loop"""
        self.running = True
        while self.running:
            try:
                await self._sync_batch()
                self.backoff.reset()
                await asyncio.sleep(self.flush_interval)
            except Exception as e:
                delay = self.backoff.get_delay()
                print(f"Sync failed: {e}. Retrying in {delay}s")
                await asyncio.sleep(delay)
    
    def stop(self) -> None:
        """Stop sync loop"""
        self.running = False
    
    async def _sync_batch(self) -> None:
        """Sync one batch of events"""
        # Get last synced offset
        start_offset = self.wal.get_sync_offset()
        
        # Read batch
        events_with_offsets = self.wal.read(start_offset, self.batch_size)
        
        if not events_with_offsets:
            return
        
        offsets, events = zip(*events_with_offsets)
        last_offset = offsets[-1] + 1  # Next start position
        
        # Send to backend
        response = await self.client.post(
            "/v1/events/batch",
            json={
                "events": [e.model_dump() for e in events]
            }
        )
        
        if response.status_code == 200:
            # Success - update offset
            self.wal.update_sync_offset(last_offset)
        elif response.status_code == 400:
            # Bad request - move to DLQ
            await self._move_to_dlq(events, response.text)
            self.wal.update_sync_offset(last_offset)
        elif response.status_code == 409:
            # Conflict (duplicates) - skip, they're already processed
            self.wal.update_sync_offset(last_offset)
        else:
            # Retryable error
            raise Exception(f"HTTP {response.status_code}: {response.text}")
    
    async def _move_to_dlq(self, events: list[BaseEvent], error: str) -> None:
        """Move failed events to dead letter queue"""
        with open(self.dlq_path, "a") as f:
            for event in events:
                f.write(json.dumps({
                    "event": event.model_dump(),
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat()
                }) + "\n")
    
    async def flush(self) -> None:
        """Force sync all pending events"""
        while True:
            start_offset = self.wal.get_sync_offset()
            events = self.wal.read(start_offset, self.batch_size)
            if not events:
                break
            await self._sync_batch()
    
    async def close(self) -> None:
        """Graceful shutdown"""
        self.stop()
        await self.flush()
        await self.client.aclose()
```

---

## Main Client API

```python
# researchos/client.py

import os
import asyncio
import atexit
import threading
from pathlib import Path
from uuid import UUID, uuid4
from typing import Optional, Any, Union
from datetime import datetime

from .wal import WAL
from .sync import SyncEngine
from .protocol.events import (
    ExperimentStartedEvent,
    RunStartedEvent,
    RunCompletedEvent,
    MetricLoggedEvent,
    ParameterSetEvent,
    ArtifactUploadedEvent,
    GitCommitEvent,
)

class ResearchOSClient:
    """
    Main SDK client.
    
    Usage:
        client = ResearchOSClient(api_key="...", organization_id="...")
        client.init_experiment("my-experiment", project="my-project")
        client.log_metric("accuracy", 0.95)
        client.finish()
    """
    
    _instance: Optional['ResearchOSClient'] = None
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        offline: bool = False,
    ):
        self.api_url = api_url or os.getenv("RESEARCHOS_API_URL", "https://api.researchos.ai")
        self.api_key = api_key or os.getenv("RESEARCHOS_API_KEY")
        self.organization_id = organization_id or UUID(os.getenv("RESEARCHOS_ORG_ID"))
        
        self.project_id = project_id
        self.experiment_id: Optional[UUID] = None
        self.run_id: Optional[UUID] = None
        
        self.offline = offline
        self.base_dir = Path.home() / ".researchos"
        
        self.wal: Optional[WAL] = None
        self.sync: Optional[SyncEngine] = None
        self.sync_thread: Optional[threading.Thread] = None
        
        # Auto-loggers
        self.auto_loggers = []
        
        # Register cleanup
        atexit.register(self._cleanup)
    
    @classmethod
    def get_instance(cls) -> 'ResearchOSClient':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def init_experiment(
        self,
        name: str,
        project: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        config: Optional[dict] = None,
    ) -> UUID:
        """
        Initialize a new experiment.
        
        Returns:
            Experiment ID
        """
        # Resolve project
        if project and isinstance(project, str):
            # Lookup project by name (or use default)
            self.project_id = self._resolve_project(project)
        
        # Generate experiment ID
        self.experiment_id = uuid4()
        
        # Initialize WAL
        self.wal = WAL(
            base_dir=self.base_dir,
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id
        )
        
        # Emit experiment started event
        event = ExperimentStartedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            name=name,
            description=description,
            tags=tags or []
        )
        self.wal.append(event)
        
        # Start sync engine (background)
        if not self.offline:
            self._start_sync()
        
        # Start auto-loggers
        self._start_auto_loggers(config)
        
        return self.experiment_id
    
    def start_run(
        self,
        parameters: Optional[dict] = None,
        git_commit: Optional[str] = None,
    ) -> UUID:
        """
        Start a new run within the experiment.
        
        Returns:
            Run ID
        """
        self.run_id = uuid4()
        
        # Auto-detect git info
        git_info = self._get_git_info() if git_commit is None else {"commit_sha": git_commit}
        
        # Emit run started event
        event = RunStartedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            run_number=self._get_next_run_number(),
            git_commit=git_info.get("commit_sha"),
            parameters=parameters or {}
        )
        self.wal.append(event)
        
        return self.run_id
    
    def log_metric(
        self,
        key: str,
        value: float,
        step: Optional[int] = None,
        wall_time: Optional[float] = None,
        **metadata: Any
    ) -> None:
        """Log a metric value"""
        if not self.run_id:
            raise RuntimeError("No active run. Call start_run() first.")
        
        event = MetricLoggedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            key=key,
            value=value,
            step=step or self._get_step(key),
            wall_time=wall_time or time.time(),
            metadata=metadata
        )
        self.wal.append(event)
    
    def log_parameter(self, key: str, value: Any) -> None:
        """Log a parameter"""
        event = ParameterSetEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            key=key,
            value=str(value),
            value_type=self._infer_type(value)
        )
        self.wal.append(event)
    
    def log_artifact(
        self,
        path: Union[str, Path],
        name: Optional[str] = None,
        artifact_type: str = "file",
    ) -> UUID:
        """
        Log an artifact (file).
        
        Returns:
            Artifact ID
        """
        path = Path(path)
        artifact_id = uuid4()
        
        # Calculate hash
        hash_sha256 = self._hash_file(path)
        
        # Emit artifact uploaded event
        event = ArtifactUploadedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            artifact_id=artifact_id,
            name=name or path.name,
            artifact_type=artifact_type,
            mime_type=self._guess_mime_type(path),
            size_bytes=path.stat().st_size,
            hash_sha256=hash_sha256
        )
        self.wal.append(event)
        
        # Upload file (async if online)
        if not self.offline:
            self._upload_artifact_async(artifact_id, path)
        
        return artifact_id
    
    def finish(self, status: str = "completed", error: Optional[str] = None) -> None:
        """Finish the current run"""
        if not self.run_id:
            return
        
        event = RunCompletedEvent(
            organization_id=self.organization_id,
            project_id=self.project_id,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            status=status,
            error=error
        )
        self.wal.append(event)
        
        self.run_id = None
    
    def _start_sync(self) -> None:
        """Start background sync thread"""
        self.sync = SyncEngine(
            api_url=self.api_url,
            api_key=self.api_key,
            wal=self.wal
        )
        
        def run_sync():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.sync.start())
        
        self.sync_thread = threading.Thread(target=run_sync, daemon=True)
        self.sync_thread.start()
    
    def _cleanup(self) -> None:
        """Cleanup on exit"""
        # Stop auto-loggers
        for logger in self.auto_loggers:
            logger.stop()
        
        # Finish run
        if self.run_id:
            self.finish()
        
        # Flush and close sync
        if self.sync:
            asyncio.run(self.sync.close())
        
        # Close WAL
        if self.wal:
            self.wal.close()
    
    # ... helper methods ...
```

---

## Auto-Logging

### System Metrics

```python
# researchos/autolog/system.py

import psutil
import threading
import time

class SystemLogger:
    """Auto-log CPU, memory, disk metrics"""
    
    def __init__(self, client: ResearchOSClient, interval: float = 5.0):
        self.client = client
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        self.running = True
        self.thread = threading.Thread(target=self._log_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _log_loop(self) -> None:
        while self.running:
            self._log_system_metrics()
            time.sleep(self.interval)
    
    def _log_system_metrics(self) -> None:
        # CPU
        self.client.log_metric("system/cpu_percent", psutil.cpu_percent())
        
        # Memory
        mem = psutil.virtual_memory()
        self.client.log_metric("system/memory_percent", mem.percent)
        self.client.log_metric("system/memory_used_gb", mem.used / 1e9)
        
        # Disk
        disk = psutil.disk_usage("/")
        self.client.log_metric("system/disk_percent", disk.percent)
```

### GPU Metrics

```python
# researchos/autolog/gpu.py

import subprocess
import threading
import time

class GPULogger:
    """Auto-log NVIDIA GPU metrics"""
    
    def __init__(self, client: ResearchOSClient, interval: float = 5.0):
        self.client = client
        self.interval = interval
        self.running = False
    
    def start(self) -> None:
        self.running = True
        threading.Thread(target=self._log_loop, daemon=True).start()
    
    def _log_loop(self) -> None:
        while self.running:
            self._log_gpu_metrics()
            time.sleep(self.interval)
    
    def _log_gpu_metrics(self) -> None:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu", 
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.strip().split("\n"):
                idx, util, mem_used, mem_total, temp = line.split(", ")
                
                self.client.log_metric(f"gpu/{idx}/utilization", float(util))
                self.client.log_metric(f"gpu/{idx}/memory_used_gb", float(mem_used) / 1e6)
                self.client.log_metric(f"gpu/{idx}/memory_percent", float(mem_used) / float(mem_total) * 100)
                self.client.log_metric(f"gpu/{idx}/temperature", float(temp))
        
        except Exception:
            pass  # No GPU or nvidia-smi not available
```

### PyTorch Hooks

```python
# researchos/autolog/pytorch.py

import torch

class PyTorchLogger:
    """Auto-log PyTorch model gradients and parameters"""
    
    def __init__(self, client: ResearchOSClient, model: torch.nn.Module, log_freq: int = 100):
        self.client = client
        self.model = model
        self.log_freq = log_freq
        self.step = 0
        
        self._register_hooks()
    
    def _register_hooks(self) -> None:
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                param.register_hook(lambda grad, n=name: self._log_gradient(n, grad))
    
    def _log_gradient(self, name: str, grad: torch.Tensor) -> torch.Tensor:
        self.step += 1
        
        if self.step % self.log_freq == 0:
            self.client.log_metric(f"grad/{name}/norm", grad.norm().item())
            self.client.log_metric(f"grad/{name}/mean", grad.mean().item())
            self.client.log_metric(f"grad/{name}/std", grad.std().item())
        
        return grad
```

---

## Convenience API

```python
# researchos/__init__.py

from .client import ResearchOSClient

_client: ResearchOSClient = None

def init(
    experiment: str,
    project: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> None:
    """Initialize ResearchOS"""
    global _client
    _client = ResearchOSClient(api_key=api_key, **kwargs)
    _client.init_experiment(experiment, project=project)

def log_metric(key: str, value: float, step: Optional[int] = None, **metadata) -> None:
    """Log a metric"""
    if _client is None:
        raise RuntimeError("Call ros.init() first")
    _client.log_metric(key, value, step=step, **metadata)

def log_parameters(params: dict) -> None:
    """Log multiple parameters"""
    for key, value in params.items():
        _client.log_parameter(key, value)

def log_artifact(path: str, name: Optional[str] = None, artifact_type: str = "file") -> None:
    """Log an artifact"""
    _client.log_artifact(path, name=name, artifact_type=artifact_type)

def finish(status: str = "completed") -> None:
    """Finish the run"""
    if _client:
        _client.finish(status=status)
```

---

## Idempotency & Exactly-Once

The SDK guarantees exactly-once delivery through:

1. **Client-generated event_id**: Every event gets a unique UUID on creation
2. **Server-side deduplication**: Backend checks `event_id` uniqueness before committing
3. **WAL offset tracking**: Client tracks last successfully synced offset
4. **Retries with same event_id**: On network failure, retry same events (same IDs)

```python
# Backend deduplication (pseudo-code)
async def handle_batch(events: list[Event]):
    for event in events:
        existing = await db.events.find_one({"event_id": event.event_id})
        if existing:
            continue  # Skip duplicate
        
        await db.events.insert_one(event)
```

---

## Backpressure Handling

```python
# researchos/utils/backoff.py

import random
import time

class ExponentialBackoff:
    """Exponential backoff with jitter"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.attempt = 0
    
    def get_delay(self) -> float:
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        if self.jitter:
            delay = delay * (0.5 + random.random())
        self.attempt += 1
        return delay
    
    def reset(self) -> None:
        self.attempt = 0
```

---

## Error Handling

### Dead Letter Queue (DLQ)

Events that cannot be processed are written to `.dlq` file:

```json
{"event": {...}, "error": "Schema validation failed", "timestamp": "2024-01-15T10:30:00Z"}
```

Users can inspect and retry DLQ events manually:

```bash
ros dlq list --experiment <exp_id>
ros dlq retry --experiment <exp_id>
```

---

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| `log_metric()` | < 1ms | WAL append + fsync |
| `log_artifact()` | < 1ms (metadata) | Upload async in background |
| `init()` | < 10ms | File creation |
| `finish()` | < 5s | Flush pending events |

---

## CLI Tools

```bash
# Initialize experiment from CLI
ros init my-experiment --project my-project

# View sync status
ros status

# Manually flush pending events
ros flush

# View DLQ
ros dlq list

# Replay events to different org
ros replay --source ~/.researchos/events/org1/proj/exp.jsonl --target org2
```

---

## Configuration

```python
# Environment variables
RESEARCHOS_API_URL=https://api.researchos.ai
RESEARCHOS_API_KEY=rsk_live_xxxxx
RESEARCHOS_ORG_ID=org_xxxxx

# Config file (~/.researchos/config.yaml)
api_url: https://api.researchos.ai
api_key: rsk_live_xxxxx
organization_id: org_xxxxx
default_project: proj_xxxxx

sync:
  batch_size: 100
  flush_interval: 5.0
  max_retries: 10

autolog:
  system: true
  gpu: true
  interval: 5.0
```

---

## Next Steps

- Event architecture → [09-event-architecture.md](./09-event-architecture.md)
- API implementation → Backend `/v1/events/batch` endpoint
