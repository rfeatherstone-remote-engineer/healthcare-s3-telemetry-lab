import json
import tempfile
import unittest
from pathlib import Path

from remediation.self_healer import SelfHealer


class TestSelfHealer(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        base = Path(self.tmp_dir.name)
        self.state_file = str(base / "cooldown.json")
        self.audit_log = str(base / "audit.jsonl")
        self.artifact_dir = str(base / "artifacts")
        self.sample_alert = {
            "alert_id": "ALT-HIPAA-PHI",
            "severity": "CRITICAL",
            "runbook": "RB-001",
            "auto_remediation": "QUARANTINE_RAW_STREAM_AND_NOTIFY_PRIVACY_OFFICER",
            "message": "Unredacted PHI detected in telemetry stream",
        }

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_defaults_to_dry_run_and_writes_audit_log(self) -> None:
        healer = SelfHealer(
            execute=False,
            state_file=self.state_file,
            audit_log=self.audit_log,
            artifact_dir=self.artifact_dir,
        )
        result = healer.process_alert(self.sample_alert, now=1000.0)
        self.assertEqual(result["status"], "DRY_RUN_SIMULATED")
        self.assertFalse((Path(self.artifact_dir) / "hipaa_stream_quarantine.flag").exists())

        lines = Path(self.audit_log).read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        logged = json.loads(lines.pop(0))
        self.assertEqual(logged["mode"], "DRY_RUN")

    def test_execute_mode_creates_artifact_and_trips_cooldown(self) -> None:
        healer = SelfHealer(
            execute=True,
            cooldown_seconds=300,
            state_file=self.state_file,
            audit_log=self.audit_log,
            artifact_dir=self.artifact_dir,
        )
        first = healer.process_alert(self.sample_alert, now=1000.0)
        self.assertEqual(first["status"], "EXECUTED")
        self.assertTrue((Path(self.artifact_dir) / "hipaa_stream_quarantine.flag").exists())

        second = healer.process_alert(self.sample_alert, now=1050.0)
        self.assertEqual(second["status"], "SUPPRESSED_CIRCUIT_BREAKER")
        self.assertIn("250.0s", second["detail"])

        after_cooldown = healer.process_alert(self.sample_alert, now=1301.0)
        self.assertEqual(after_cooldown["status"], "EXECUTED")


if __name__ == "__main__":
    unittest.main()
