# Blameless Post-Mortem & SLO Impact Report

- **Incident ID:** {{INCIDENT_ID}}
- **Service Affected:** {{SERVICE_NAME}}
- **Severity:** {{SEVERITY}}

## 1. Key Reliability Metrics
- **Time to Detect (TTD):** {{TTD_MINUTES}} minutes
- **Time to Mitigate (TTM):** {{TTM_MINUTES}} minutes
- **Total Downtime:** {{TOTAL_DOWNTIME_MINUTES}} minutes
- **30-Day SLO Target (99.9%):** 43.2 minutes allowed budget
- **Error Budget Consumed:** {{BUDGET_CONSUMED_PCT}}% ({{REMAINING_BUDGET_MINUTES}} minutes remaining)

## 2. Executive Summary (Systemic Focus)
{{SUMMARY}}

## 3. Root Cause & Contributing Factors
- {{ROOT_CAUSE}}

## 4. Action Items (Paved Road Improvements)
- [ ] Add automated pre-deploy guardrails to prevent recurrence.
- [ ] Update synthetic monitoring thresholds to reduce TTD.
