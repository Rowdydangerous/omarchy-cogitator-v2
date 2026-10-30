#!/usr/bin/env python3
"""Small read-only Linux telemetry snapshot for the Auspex console."""
import json
import os
from pathlib import Path


def snapshot(proc=Path("/proc"), home=None):
    result = {"cpu": None, "memory": None, "disk": None, "uptime": None}
    try:
        fields = (proc / "stat").read_text().splitlines()[0].split()
        # guest/guest_nice are already included in user/nice; do not add twice.
        ticks = [int(value) for value in fields[1:9]]
        if fields[0] == "cpu" and len(ticks) >= 4:
            result["cpu"] = {"idle": ticks[3] + (ticks[4] if len(ticks) > 4 else 0), "total": sum(ticks)}
    except (OSError, ValueError, IndexError):
        pass
    try:
        memory = {line.split(":", 1)[0]: int(line.split()[1]) for line in (proc / "meminfo").read_text().splitlines()}
        total, available = memory["MemTotal"], memory["MemAvailable"]
        if total > 0 and 0 <= available <= total:
            used = total - available
            result["memory"] = {"percent": round(100 * used / total),
                                "text": f"{used / 1048576:.1f} / {total / 1048576:.1f} GiB"}
    except (OSError, ValueError, KeyError, IndexError):
        pass
    try:
        fs = os.statvfs(home or Path.home())
        used, available = fs.f_blocks - fs.f_bfree, fs.f_bavail
        if used + available > 0:
            result["disk"] = {"percent": round(100 * used / (used + available)),
                              "freeGiB": round(available * fs.f_frsize / 1073741824, 1)}
    except OSError:
        pass
    try:
        result["uptime"] = float((proc / "uptime").read_text().split()[0])
    except (OSError, ValueError, IndexError):
        pass
    return result


if __name__ == "__main__":
    print(json.dumps(snapshot()))
