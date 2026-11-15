#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path

MONTHLY_BUDGET_99_9 = 43.2

def calculate_slo_metrics(incident_start: str, detected_at: str, mitigated_at: str) -> dict:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    t_start = datetime.strptime(incident_start, fmt)
    t_detect = datetime.strptime(detected_at, fmt)
    t_mitigate = datetime.strptime(mitigated_at, fmt)

    ttd_min = round((t_detect - t_start).total_seconds() / 60, 2)
    ttm_min = round((t_mitigate - t_detect).total_seconds() / 60, 2)
    total_down = round((t_mitigate - t_start).total_seconds() / 60, 2)

    budget_consumed_pct = round((total_down / MONTHLY_BUDGET_99_9) * 100, 2)
    remaining_min = round(max(0.0, MONTHLY_BUDGET_99_9 - total_down), 2)

    return {
        "ttd_minutes": ttd_min,
        "ttm_minutes": ttm_min,
        "total_downtime_minutes": total_down,
        "budget_consumed_pct": budget_consumed_pct,
        "remaining_budget_minutes": remaining_min,
    }

def render_report(template_path: Path, incident_id: str, service: str, metrics: dict) -> str:
    content = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{INCIDENT_ID}}": incident_id,
        "{{SERVICE_NAME}}": service,
        "{{SEVERITY}}": "SEV-2",
        "{{TTD_MINUTES}}": str(metrics["ttd_minutes"]),
        "{{TTM_MINUTES}}": str(metrics["ttm_minutes"]),
        "{{TOTAL_DOWNTIME_MINUTES}}": str(metrics["total_downtime_minutes"]),
        "{{BUDGET_CONSUMED_PCT}}": str(metrics["budget_consumed_pct"]),
        "{{REMAINING_BUDGET_MINUTES}}": str(metrics["remaining_budget_minutes"]),
        "{{SUMMARY}}": "Automated memory pressure triggered graceful degradation without PHI exposure.",
        "{{ROOT_CAUSE}}": "Missing memory ceiling alert on worker node prior to traffic spike.",
    }
    for placeholder, val in replacements.items():
        content = content.replace(placeholder, val)
    return content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Blameless RCA Report")
    parser.add_argument("--id", default="INC-2026-042")
    parser.add_argument("--service", default="care-coordination-api")
    parser.add_argument("--start", default="2026-11-14T14:00:00Z")
    parser.add_argument("--detected", default="2026-11-14T14:04:00Z")
    parser.add_argument("--mitigated", default="2026-11-14T14:14:48Z")
    args = parser.parse_args()

    slo_data = calculate_slo_metrics(args.start, args.detected, args.mitigated)
    tpl = Path(__file__).resolve().parent.parent / "templates" / "blameless_rca.md"
    print(render_report(tpl, args.id, args.service, slo_data))
