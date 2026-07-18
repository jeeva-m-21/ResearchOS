"""Background monitor thread for automatic system/GPU metric collection.

The AutoLogger polls system and GPU metrics at a configurable interval
and logs them as experiment metrics via a provided log function.
"""

import threading
import time
from typing import Callable, Dict, Optional

from .gpu import GPUCollector
from .system import collect_all


class AutoLogger:
    """Background thread that polls system/GPU metrics and logs via a callback.

    Usage:
        def log_fn(key, value, step): ...
        monitor = AutoLogger(log_fn)
        monitor.start(interval=5.0)
        ...
        monitor.stop()
    """

    def __init__(
        self,
        log_metric_fn: Callable[[str, float, Optional[int]], None],
    ) -> None:
        """
        Args:
            log_metric_fn: A callable with signature (key, value, step).
                Typically ``client.log_metric`` or ``experiment.log_metric``.
        """
        self._log_metric = log_metric_fn
        self._gpu = GPUCollector()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._interval = 5.0
        self._step_counters: Dict[str, int] = {}

    def start(self, interval: float = 5.0) -> None:
        """Start the background monitor thread.

        Args:
            interval: Seconds between metric polls.
        """
        if self._running:
            return
        self._interval = interval
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background monitor thread and wait for it to finish."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    @property
    def is_running(self) -> bool:
        """Whether the monitor thread is currently active."""
        return self._running

    def _run(self) -> None:
        """Main monitor loop — polls and logs metrics at the configured interval."""
        while self._running:
            try:
                metrics = collect_all()

                # Add GPU metrics if available
                gpu_metrics = self._gpu.collect()
                metrics.update(gpu_metrics)

                # Log each metric with auto-incremented step
                for key, value in metrics.items():
                    self._step_counters[key] = self._step_counters.get(key, 0) + 1
                    step = self._step_counters[key]
                    self._log_metric(key, value, step)

            except Exception:
                # Don't crash the monitor thread on transient errors
                pass

            # Sleep in small increments so stop() is responsive
            sleep_iters = max(int(self._interval * 10), 1)
            for _ in range(sleep_iters):
                if not self._running:
                    break
                time.sleep(0.1)
