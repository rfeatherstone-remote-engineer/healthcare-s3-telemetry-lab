# Runbook RB-002: Upstream PHI Leak Intercepted
- **Alert ID:** `ALT-HIPAA-PHI`
- **Containment:** Verify downstream sinks received only `[REDACTED-*]` tokens; disable verbose debug logging on emitting service without echoing raw payloads.
- **Remediation:** Strip PHI at structured logger serializer and add regression test to `tests/test_compliance.py`.
- **Escalation:** Notify Healthcare Privacy Officer within 1 hour with TTD/TTM window.
