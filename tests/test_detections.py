import unittest
from detections.alert_rules import evaluate_telemetry

class TestAutomatedDetections(unittest.TestCase):
    def test_healthy_telemetry_triggers_no_alerts(self):
        rec = {"host": "hipaa-node-01", "memory_used_pct": 42.5, "cpu_load_1m": 0.45, "phi_redacted_count": 0}
        self.assertEqual(len(evaluate_telemetry(rec)), 0)

    def test_critical_thresholds_trigger_linked_runbooks(self):
        rec = {"host": "hipaa-node-01", "memory_used_pct": 91.2, "cpu_load_1m": 2.4, "phi_redacted_count": 3, "guardrail_drift_detected": True}
        alerts = evaluate_telemetry(rec)
        self.assertEqual({a["alert_id"] for a in alerts}, {"ALT-MEM-CRIT", "ALT-CPU-CRIT", "ALT-HIPAA-PHI", "ALT-S3-DRIFT"})
        self.assertIn("runbooks/RB-002-phi-leak-detected.md", {a["runbook"] for a in alerts})

    def test_masked_message_markers_trigger_phi_alert(self):
        rec = {"host": "hipaa-node-01", "memory_used_pct": 30.0, "cpu_load_1m": 0.2, "message": "SSN [REDACTED-SSN]"}
        alerts = evaluate_telemetry(rec)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(next(iter(alerts))["alert_id"], "ALT-HIPAA-PHI")

if __name__ == "__main__":
    unittest.main()
