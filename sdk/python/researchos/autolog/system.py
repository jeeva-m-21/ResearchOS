"""System metrics collectors using psutil.

Collects CPU, memory, and disk usage metrics for automatic logging
as experiment metrics (prefixed with 'sys/').
"""

from typing import Dict

import psutil


def collect_cpu() -> Dict[str, float]:
    """Collect CPU metrics.

    Returns:
        dict with keys: percent, count, freq_current_mhz (optional)
    """
    metrics: Dict[str, float] = {}
    metrics["percent"] = psutil.cpu_percent(interval=0.1)
    count_val = psutil.cpu_count()
    if count_val is not None:
        metrics["count"] = float(count_val)
    freq = psutil.cpu_freq()
    if freq is not None:
        current = freq.current
        if current is not None:
            metrics["freq_current_mhz"] = float(current)
    return metrics


def collect_memory() -> Dict[str, float]:
    """Collect memory metrics.

    Returns:
        dict with keys: total_gb, available_gb, used_gb, percent
    """
    mem = psutil.virtual_memory()
    return {
        "total_gb": mem.total / (1024 ** 3),
        "available_gb": mem.available / (1024 ** 3),
        "used_gb": (mem.total - mem.available) / (1024 ** 3),
        "percent": mem.percent,
    }


def collect_disk(path: str = "/") -> Dict[str, float]:
    """Collect disk usage metrics.

    Args:
        path: Mount point to check (default: root).

    Returns:
        dict with keys: total_gb, used_gb, free_gb, percent
    """
    disk = psutil.disk_usage(path)
    return {
        "total_gb": disk.total / (1024 ** 3),
        "used_gb": disk.used / (1024 ** 3),
        "free_gb": disk.free / (1024 ** 3),
        "percent": disk.percent,
    }


def collect_all() -> Dict[str, float]:
    """Collect all system metrics.

    Returns:
        Flat dict with 'sys/' prefix for each metric key.
        e.g. {'sys/cpu_percent': 45.2, 'sys/memory_percent': 62.1, ...}
    """
    metrics: Dict[str, float] = {}

    cpu = collect_cpu()
    metrics["sys/cpu_percent"] = cpu["percent"]
    metrics["sys/cpu_count"] = cpu["count"]
    if "freq_current_mhz" in cpu:
        metrics["sys/cpu_freq_mhz"] = cpu["freq_current_mhz"]

    mem = collect_memory()
    metrics["sys/memory_total_gb"] = round(mem["total_gb"], 2)
    metrics["sys/memory_available_gb"] = round(mem["available_gb"], 2)
    metrics["sys/memory_used_gb"] = round(mem["used_gb"], 2)
    metrics["sys/memory_percent"] = mem["percent"]

    disk = collect_disk()
    metrics["sys/disk_total_gb"] = round(disk["total_gb"], 2)
    metrics["sys/disk_used_gb"] = round(disk["used_gb"], 2)
    metrics["sys/disk_free_gb"] = round(disk["free_gb"], 2)
    metrics["sys/disk_percent"] = disk["percent"]

    return metrics
