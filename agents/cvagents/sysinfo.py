"""Informazioni sulla macchina: quanta RAM c'è (Linux, macOS, Windows)."""
import ctypes
import subprocess
import sys

GIB = 1024 ** 3


def ram_linux():
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024 / GIB
    raise RuntimeError("MemTotal non trovato")


def ram_macos():
    return int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True).stdout) / GIB


def ram_windows():
    class Status(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                    ("avail", ctypes.c_ulonglong), ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong),
                    ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("ave", ctypes.c_ulonglong)]
    status = Status(length=ctypes.sizeof(Status))
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.total / GIB


def total_ram_gb():
    """RAM totale in GiB; 0 se non si riesce a leggerla (si userà il modello più piccolo)."""
    reader = {"linux": ram_linux, "darwin": ram_macos, "win32": ram_windows}.get(sys.platform)
    try:
        return reader() if reader else 0.0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        return 0.0
