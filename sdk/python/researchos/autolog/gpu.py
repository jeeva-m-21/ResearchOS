"""GPU metrics collector with graceful fallback when no GPU is available.

Uses nvidia-smi via subprocess to query GPU stats.
Gracefully degrades when no NVIDIA GPU or nvidia-smi is present.
"""

import shutil
import subprocess
from typing import Dict, Optional


class GPUCollector:
    """GPU metrics collector via nvidia-smi.

    Queries GPU utilization, memory usage, and temperature.
    Returns empty dict when no GPU is available (no crash).
    """

    def __init__(self) -> None:
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Check if nvidia-smi is available and GPUs are present."""
        if self._available is not None:
            return self._available

        if shutil.which("nvidia-smi") is None:
            self._available = False
            return False

        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            self._available = result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            self._available = False

        return self._available

    def collect(self) -> Dict[str, float]:
        """Collect GPU metrics.

        Returns:
            Flat dict with 'gpu/' prefix keys. Empty dict if no GPU available.
            e.g. {'gpu/0_util_percent': 85.0, 'gpu/0_memory_used_gb': 4.2, ...}
        """
        if not self.available:
            return {}

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )

            metrics: Dict[str, float] = {}
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    idx = parts[0]
                    try:
                        metrics[f"gpu/{idx}_util_percent"] = float(parts[1])
                        mem_used_gb = float(parts[2]) / 1024.0
                        metrics[f"gpu/{idx}_memory_used_gb"] = round(mem_used_gb, 2)
                        mem_total_gb = float(parts[3]) / 1024.0
                        metrics[f"gpu/{idx}_memory_total_gb"] = round(mem_total_gb, 2)
                        metrics[f"gpu/{idx}_temp_celsius"] = float(parts[4])
                    except (ValueError, IndexError):
                        # Skip malformed lines
                        continue
            return metrics

        except Exception:
            return {}
