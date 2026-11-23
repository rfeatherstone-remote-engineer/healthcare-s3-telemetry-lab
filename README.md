[![CI](https://github.com/rfeatherstone-remote-engineer/healthcare-s3-telemetry-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/rfeatherstone-remote-engineer/healthcare-s3-telemetry-lab/actions/workflows/ci.yml)

# Healthcare SRE Telemetry & PHI Compliance Lab

A zero-dependency Python 3 observability, HIPAA Safe Harbor PHI redaction, and blameless post-mortem automation suite designed for low-footprint Linux hosts.

## Pipeline Architecture
1. **System Telemetry (`core/system_monitor.py`):** Reads `/proc/meminfo` and CPU load averages directly via standard library calls and emits structured JSON logs.
2. **Real-Time PHI Sanitizer (`compliance/phi_sanitizer.py`):** Filters streaming JSON over Unix pipes (`stdin -> stdout`), masking SSNs, MRNs, emails, and phone numbers (`HIPAA § 164.514(b)(2)`).
3. **Blameless RCA & SLO Calculator (`compliance/postmortem_gen.py`):** Computes Time to Detect (`TTD`), Time to Mitigate (`TTM`), and 30-day `99.9%` SLO error-budget burn (`43.2` minutes allowed downtime).

## Quick Usage
```bash
python3 core/system_monitor.py | python3 compliance/phi_sanitizer.py | jq .
python3 compliance/postmortem_gen.py
python3 -m unittest discover -s tests -v
```

## Level 3: Bounded Self-Healing Executor (`remediation/self_healer.py`)

Consumes alert JSON objects over a Unix pipe (`stdin -> stdout`) and applies idempotent, low-blast-radius containment actions with strict SRE safety guardrails:

- **Safe `--dry-run` Default:** Simulates remediation decisions and writes audit entries without altering host state unless `--execute` is explicitly passed.
- **Cooldown Circuit Breaker:** Enforces a configurable cooldown window (default `300s` per `alert_id`) with atomic state persistence to prevent flapping alerts from triggering remediation storms.
- **Immutable JSONL Audit Trail:** Records every decision (`DRY_RUN_SIMULATED`, `EXECUTED`, `SUPPRESSED_CIRCUIT_BREAKER`, `SKIPPED_NO_ACTION`) with timestamps and linked runbook IDs.

## Pipeline Diagram

```text
  [ Linux /proc Telemetry ] ──► [ HIPAA Safe Harbor PHI Redactor ]
                                              │
                                              ▼
  [ JSONL Audit & Blameless RCA ] ◄── [ 300s Cooldown Self-Healer ]
```

## Sample CLI Output

```json
{
  "decision": "DRY_RUN_SIMULATED",
  "phi_redacted": ["SSN", "MRN", "EMAIL", "PHONE"],
  "slo_target": 0.999,
  "error_budget_minutes": 43.2
}
```
