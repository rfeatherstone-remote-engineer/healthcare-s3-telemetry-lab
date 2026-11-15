# Runbook RB-001: Host Memory & CPU Saturation Triage
- **Alert IDs:** `ALT-MEM-CRIT`, `ALT-MEM-WARN`, `ALT-CPU-CRIT`
- **Triage:** Run `free -m && head -n 10 /proc/meminfo` and `ps -eo pid,cmd,%mem,%cpu --sort=-%mem | head -n 15`.
- **Mitigation:** Restart leaking non-critical service (`sudo systemctl restart <service>`) and verify `memory_used_pct < 70%`.
- **Escalation:** Cordon node and page Platform On-Call Lead if `MemAvailable < 10%`.
