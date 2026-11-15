# Runbook RB-003: HIPAA S3 Guardrail Drift
- **Alert ID:** `ALT-S3-DRIFT`
- **Triage:** Query CloudTrail (`aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::S3::Bucket`) to identify non-Terraform IAM principal.
- **Reconciliation:** Run `terraform init -backend=false && terraform validate` in `hipaa-s3-golden-path` and re-apply via approved CI/CD.
- **Escalation:** Revoke unauthorized session credentials and escalate to Cloud Security Engineering.
