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
