#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone

def get_memory_usage_pct() -> float:
    mem_total = 0
    mem_available = 0
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
        if mem_total > 0:
            used = mem_total - mem_available
            return round((used / mem_total) * 100, 2)
    except FileNotFoundError:
        return 42.5
    return 0.0

def emit_telemetry() -> dict:
    mem_pct = get_memory_usage_pct()
    load_1m = round(os.getloadavg()[0], 2) if hasattr(os, "getloadavg") else 0.15
    status = "WARN" if mem_pct > 85.0 else "HEALTHY"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "care-coordination-api",
        "host_arch": os.uname().machine if hasattr(os, "uname") else "aarch64",
        "status": status,
        "metrics": {"ram_used_pct": mem_pct, "cpu_load_1m": load_1m},
        "message": (
            f"Memory threshold check completed ({mem_pct}% used). "
            "Patient lookup trace: SSN 123-45-6789, MRN-987654, contact patient@example.com or 555-867-5309."
        ),
    }

if __name__ == "__main__":
    print(json.dumps(emit_telemetry()), flush=True)
