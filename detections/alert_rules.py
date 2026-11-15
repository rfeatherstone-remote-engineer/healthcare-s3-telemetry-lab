#!/usr/bin/env python3
import json, sys
from typing import Any, Dict, List

DEFAULT_THRESHOLDS = {
    "memory_used_pct_critical": 85.0,
    "memory_used_pct_warning": 75.0,
    "cpu_load_1m_critical": 2.0,
    "phi_redacted_critical": 1,
}

def _extract_phi_count(record: Dict[str, Any]) -> int:
    for key in ("phi_redacted_count", "redaction_count", "phi_scrubbed_count"):
        if key in record and record[key] is not None:
            return int(record[key])
    msg = str(record.get("message", ""))
    if "[REDACTED-" in msg:
        return msg.count("[REDACTED-")
    if record.get("phi_redacted") is True or record.get("phi_scrubbed") is True:
        return 1
    return 0

def evaluate_telemetry(record: Dict[str, Any], thresholds: Dict[str, float] = DEFAULT_THRESHOLDS) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    host, ts = record.get("host", "unknown-host"), record.get("timestamp", "")
    mem_pct = float(record.get("memory_used_pct", 0.0))
    cpu_1m = float(record.get("cpu_load_1m", 0.0))
    phi_count = _extract_phi_count(record)
    drift = bool(record.get("guardrail_drift_detected", False))

    if mem_pct >= thresholds["memory_used_pct_critical"]:
        alerts.append({"alert_id": "ALT-MEM-CRIT", "severity": "CRITICAL", "host": host, "timestamp": ts,
            "summary": f"Memory saturation at {mem_pct:.1f}%", "runbook": "runbooks/RB-001-memory-saturation.md",
            "auto_remediation": "TRIGGER_NON_CRITICAL_CACHE_FLUSH_AND_PAGE_ONCALL"})
    elif mem_pct >= thresholds["memory_used_pct_warning"]:
        alerts.append({"alert_id": "ALT-MEM-WARN", "severity": "WARNING", "host": host, "timestamp": ts,
            "summary": f"Elevated memory at {mem_pct:.1f}%", "runbook": "runbooks/RB-001-memory-saturation.md",
            "auto_remediation": "LOG_PROCESS_SNAPSHOT"})

    if cpu_1m >= thresholds["cpu_load_1m_critical"]:
        alerts.append({"alert_id": "ALT-CPU-CRIT", "severity": "CRITICAL", "host": host, "timestamp": ts,
            "summary": f"1-min CPU load at {cpu_1m:.2f}", "runbook": "runbooks/RB-001-memory-saturation.md",
            "auto_remediation": "CAPTURE_TOP_CPU_THREADS"})

    if phi_count >= thresholds["phi_redacted_critical"]:
        alerts.append({"alert_id": "ALT-HIPAA-PHI", "severity": "CRITICAL", "host": host, "timestamp": ts,
            "summary": f"Upstream PHI leak intercepted ({phi_count} identifiers scrubbed)",
            "runbook": "runbooks/RB-002-phi-leak-detected.md",
            "auto_remediation": "QUARANTINE_RAW_STREAM_AND_NOTIFY_PRIVACY_OFFICER"})

    if drift:
        alerts.append({"alert_id": "ALT-S3-DRIFT", "severity": "CRITICAL", "host": host, "timestamp": ts,
            "summary": "Unauthorized S3 guardrail drift detected",
            "runbook": "runbooks/RB-003-s3-guardrail-drift.md",
            "auto_remediation": "BLOCK_IAM_SESSION_AND_QUEUE_TERRAFORM_PLAN"})
    return alerts

def process_stream(stream) -> None:
    for raw in stream:
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        alerts = evaluate_telemetry(rec)
        print(json.dumps({"telemetry": rec, "alerts_triggered": len(alerts), "alerts": alerts}), flush=True)

if __name__ == "__main__":
    process_stream(sys.stdin)
