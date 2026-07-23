#!/usr/bin/env python3
"""Cross-platform resource probe and conservative command wrapper for Potato Mode."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any

MIB = 1024 * 1024


def _linux_memory() -> tuple[int | None, int | None]:
    try:
        values: dict[str, int] = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0]) * 1024
        return values.get("MemTotal"), values.get("MemAvailable")
    except (OSError, ValueError, IndexError):
        return None, None


def _mac_memory() -> tuple[int | None, int | None]:
    try:
        total = int(subprocess.check_output(
            ["sysctl", "-n", "hw.memsize"], text=True, stderr=subprocess.DEVNULL
        ).strip())
        output = subprocess.check_output(["vm_stat"], text=True, stderr=subprocess.DEVNULL)
        page_size = 4096
        available_pages = 0
        for line in output.splitlines():
            if "page size of" in line:
                page_size = int(line.split("page size of", 1)[1].split("bytes", 1)[0].strip())
            elif any(line.startswith(label) for label in (
                "Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"
            )):
                available_pages += int(line.split(":", 1)[1].strip().rstrip("."))
        return total, available_pages * page_size
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None, None


def _windows_memory() -> tuple[int | None, int | None]:
    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    try:
        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None, None
        return int(status.ullTotalPhys), int(status.ullAvailPhys)
    except (AttributeError, OSError):
        return None, None


def memory_bytes() -> tuple[int | None, int | None]:
    system = platform.system()
    if system == "Linux":
        return _linux_memory()
    if system == "Darwin":
        return _mac_memory()
    if system == "Windows":
        return _windows_memory()
    return None, None


def classify(available_ram: int | None, free_disk: int, cpus: int, load: float | None) -> tuple[str, int, list[str]]:
    reasons: list[str] = []
    available_mib = available_ram / MIB if available_ram is not None else None
    free_disk_mib = free_disk / MIB
    load_ratio = load / cpus if load is not None and cpus > 0 else None

    if available_mib is not None and available_mib < 1536:
        reasons.append("available memory is below 1.5 GiB")
    if free_disk_mib < 2048:
        reasons.append("free disk space is below 2 GiB")
    if load_ratio is not None and load_ratio >= 1.0:
        reasons.append("one-minute load is at or above CPU capacity")
    if reasons:
        return "critical", 1, reasons

    constrained = []
    if available_mib is not None and available_mib < 4096:
        constrained.append("available memory is below 4 GiB")
    if free_disk_mib < 6144:
        constrained.append("free disk space is below 6 GiB")
    if cpus <= 2:
        constrained.append("two or fewer CPU threads are visible")
    if load_ratio is not None and load_ratio >= 0.7:
        constrained.append("one-minute load is elevated")
    if constrained:
        return "constrained", 1, constrained

    balanced = []
    if available_mib is not None and available_mib < 8192:
        balanced.append("available memory is below 8 GiB")
    if free_disk_mib < 15360:
        balanced.append("free disk space is below 15 GiB")
    if cpus <= 4:
        balanced.append("four or fewer CPU threads are visible")
    if balanced:
        return "balanced", min(2, cpus), balanced

    return "roomy", min(4, max(1, cpus // 2)), ["current headroom supports moderate parallelism"]


def probe(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    disk = shutil.disk_usage(resolved)
    total_ram, available_ram = memory_bytes()
    cpus = os.cpu_count() or 1
    try:
        load = os.getloadavg()[0]
    except (AttributeError, OSError):
        load = None
    tier, workers, reasons = classify(available_ram, disk.free, cpus, load)
    return {
        "schema_version": 1,
        "platform": platform.system().lower() or "unknown",
        "path": str(resolved),
        "tier": tier,
        "worker_limit": workers,
        "cpu_threads": cpus,
        "load_1m": round(load, 2) if load is not None else None,
        "memory_total_mib": round(total_ram / MIB) if total_ram is not None else None,
        "memory_available_mib": round(available_ram / MIB) if available_ram is not None else None,
        "disk_free_mib": round(disk.free / MIB),
        "reasons": reasons,
    }


def human_report(data: dict[str, Any]) -> str:
    memory = data["memory_available_mib"]
    memory_text = f"{memory} MiB available" if memory is not None else "availability unknown"
    load = data["load_1m"]
    load_text = f"{load}" if load is not None else "unavailable"
    reasons = "; ".join(data["reasons"])
    return "\n".join([
        f"Potato tier: {data['tier']}",
        f"Worker limit: {data['worker_limit']}",
        f"Memory: {memory_text}",
        f"Disk free: {data['disk_free_mib']} MiB",
        f"CPU threads: {data['cpu_threads']} (1m load: {load_text})",
        f"Why: {reasons}",
    ])


def limited_environment(workers: int) -> dict[str, str]:
    env = os.environ.copy()
    values = {
        "CARGO_BUILD_JOBS": str(workers),
        "GOMAXPROCS": str(workers),
        "MAKEFLAGS": f"-j{workers}",
        "PYTEST_XDIST_AUTO_NUM_WORKERS": str(workers),
        "RAYON_NUM_THREADS": str(workers),
        "UV_CONCURRENT_BUILDS": str(workers),
        "UV_CONCURRENT_DOWNLOADS": str(workers),
    }
    for key, value in values.items():
        env[key] = value
    return env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="potato", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    probe_parser = sub.add_parser("probe", help="Report a conservative resource tier")
    probe_parser.add_argument("--path", type=Path, default=Path.cwd())
    probe_parser.add_argument("--json", action="store_true", dest="as_json")
    run_parser = sub.add_parser("run", help="Run a command with conservative worker settings")
    run_parser.add_argument("--path", type=Path, default=Path.cwd())
    run_parser.add_argument("command_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data = probe(args.path)
    if args.command == "probe":
        print(json.dumps(data, indent=2, sort_keys=True) if args.as_json else human_report(data))
        return 0
    command = args.command_args
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("potato run requires a command after --", file=sys.stderr)
        return 2
    print(f"Potato mode: {data['tier']}, limiting cooperative tools to {data['worker_limit']} worker(s).", file=sys.stderr)
    try:
        completed = subprocess.run(command, cwd=args.path, env=limited_environment(data["worker_limit"]), check=False)
        return completed.returncode
    except FileNotFoundError:
        print(f"Command not found: {command[0]}", file=sys.stderr)
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
