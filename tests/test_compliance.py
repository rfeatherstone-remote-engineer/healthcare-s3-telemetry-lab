import unittest
from compliance.phi_sanitizer import scrub_text
from compliance.postmortem_gen import calculate_slo_metrics

class TestComplianceAndSLO(unittest.TestCase):
    def test_ssn_redaction(self):
        self.assertEqual(scrub_text("Patient SSN: 123-45-6789"), "Patient SSN: [REDACTED-SSN]")

    def test_mrn_redaction(self):
        self.assertEqual(scrub_text("Record MRN-10293847 loaded"), "Record [REDACTED-MRN] loaded")

    def test_email_and_phone_redaction(self):
        raw = "Contact jane.doe@clinic.org or (614) 555-0199"
        self.assertEqual(scrub_text(raw), "Contact [REDACTED-PHI] or [REDACTED-PHI]")

    def test_slo_error_budget_math(self):
        metrics = calculate_slo_metrics(
            "2026-11-14T10:00:00Z",
            "2026-11-14T10:05:00Z",
            "2026-11-14T10:21:36Z",
        )
        self.assertEqual(metrics["ttd_minutes"], 5.0)
        self.assertEqual(metrics["ttm_minutes"], 16.6)
        self.assertEqual(metrics["total_downtime_minutes"], 21.6)
        self.assertEqual(metrics["budget_consumed_pct"], 50.0)
        self.assertEqual(metrics["remaining_budget_minutes"], 21.6)

if __name__ == "__main__":
    unittest.main()
