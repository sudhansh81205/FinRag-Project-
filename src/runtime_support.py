"""R2/R4/R13 common A-G runtime paths and measured memory, never invented defaults."""

import ctypes
import os
import platform
import subprocess
from pathlib import Path


def model_cache(root, override=None):
    """Use the build cache at startup; keep explicit and environment overrides."""
    value = override or os.environ.get("SENTENCE_TRANSFORMERS_HOME")
    return (Path(root) / (value or "output/models")).resolve()


def total_memory_bytes():
    """Read real physical memory on Windows/macOS/POSIX, or return unknown."""
    try:
        if platform.system() == "Windows":
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_uint32), ("load", ctypes.c_uint32),
                    ("total", ctypes.c_uint64), ("available", ctypes.c_uint64),
                    ("page_total", ctypes.c_uint64), ("page_available", ctypes.c_uint64),
                    ("virtual_total", ctypes.c_uint64), ("virtual_available", ctypes.c_uint64),
                    ("extended_available", ctypes.c_uint64),
                ]

            status = MemoryStatus()
            status.length = ctypes.sizeof(status)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return None
            value = status.total
        elif platform.system() == "Darwin":
            value = int(subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"], text=True, timeout=5))
        else:
            value = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        return value if isinstance(value, int) and value > 0 else None
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
        return None
