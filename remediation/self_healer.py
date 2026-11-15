#!/usr/bin/env python3
"""Closed-Loop Self-Healing Executor (Level 3 SRE Automation)."""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_COOLDOWN_SECONDS = 300
DEFAULT_BASE_DIR = os.path.join(os.path.expanduser("~"), ".local", "state", "sre_healer")
DEFAULT_STATE_FILE = os.path.join(DEFAULT_BASE_DIR, "cooldown_state.json")
DEFAULT_AUDIT_LOG = os.path.join(DEFAULT_BASE_DIR, "audit.jsonl")
DEFAULT_ARTIFACT_DIR = os.path.join(DEFAULT_BASE_DIR, "artifacts")


class SelfHealer:
    def __init__(
        self,
        execute: bool = False,
        cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS,
        state_file: str = DEFAULT_STATE_FILE,
        audit_log: str = DEFAULT_AUDIT_LOG,
        artifact_dir: str = DEFAULT_ARTIFACT_DIR,
    ) -> None:
        self.execute = execute
        self.cooldown_seconds = cooldown_seconds
        self.state_file = Path(state_file)
        self.audit_log = Path(audit_log)
        self.artifact_dir = Path(artifact_dir)

    def _ensure_private_dir(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)

    def _load_state(self) -> Dict[str, float]:
        if not self.state_file.exists():
            return {}
        try:
            with self.state_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    return {str(k): float(v) for k, v in data.items()}
        except (OSError, ValueError, TypeError):
            return {}
        return {}

    def _save_state(self, state: Dict[str, float]) -> None:
        self._ensure_private_dir(self.state_file.parent)
        tmp_path = self.state_file.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
        os.replace(tmp_path, self.state_file)

    def _write_audit_entry(self, entry: Dict[str, Any]) -> None:
        self._ensure_private_dir(self.audit_log.parent)
        with self.audit_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")

    def _check_cooldown(self, alert_id: str, now: float) -> Optional[float]:
        state = self._load_state()
        last_run = state.get(alert_id)
        if last_run is not None:
            elapsed = now - last_run
            if elapsed < self.cooldown_seconds:
                return round(self.cooldown_seconds - elapsed, 2)
        return None

    def _record_execution(self, alert_id: str, now: float) -> None:
        state = self._load_state()
        state[alert_id] = now
        self._save_state(state)

    def _perform_bounded_action(self, action: str, alert: Dict[str, Any]) -> str:
        self._ensure_private_dir(self.artifact_dir)
        alert_id = str(alert.get("alert_id", "UNKNOWN"))
        runbook = str(alert.get("runbook", "UNASSIGNED"))
        ts = datetime.now(timezone.utc).isoformat()

        if action == "QUARANTINE_RAW_STREAM_AND_NOTIFY_PRIVACY_OFFICER":
            flag_path = self.artifact_dir / "hipaa_stream_quarantine.flag"
            flag_path.write_text(
                f"QUARANTINED_AT={ts}\nALERT_ID={alert_id}\nRUNBOOK={runbook}\n",
                encoding="utf-8",
            )
            return f"Created quarantine flag at {flag_path}"

        if action == "TRIGGER_NON_CRITICAL_CACHE_FLUSH_AND_PAGE_ONCALL":
            snap_path = self.artifact_dir / "mem_triage_snapshot.json"
            payload = {
                "captured_at": ts,
                "alert_id": alert_id,
                "runbook": runbook,
                "action": "CACHE_FLUSH_QUEUED",
                "details": alert.get("message", ""),
            }
            snap_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return f"Captured memory triage snapshot at {snap_path}"

        if action == "BLOCK_IAM_SESSION_AND_QUEUE_TERRAFORM_PLAN":
            drift_path = self.artifact_dir / "terraform_reconcile.queue"
            drift_path.write_text(
                f"QUEUED_AT={ts}\nALERT_ID={alert_id}\nRUNBOOK={runbook}\n",
                encoding="utf-8",
            )
            return f"Queued drift reconciliation marker at {drift_path}"

        return f"No automated handler mapped for action '{action}'; routed to human on-call"

    def process_alert(
        self, alert: Dict[str, Any], now: Optional[float] = None
    ) -> Dict[str, Any]:
        current_ts = time.time() if now is None else now
        alert_id = str(alert.get("alert_id", "UNKNOWN"))
        severity = str(alert.get("severity", "INFO")).upper()
        action = str(alert.get("auto_remediation", "NONE"))
        runbook = str(alert.get("runbook", "UNASSIGNED"))

        decision: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(current_ts, tz=timezone.utc).isoformat(),
            "alert_id": alert_id,
            "severity": severity,
            "runbook": runbook,
            "requested_action": action,
            "mode": "EXECUTE" if self.execute else "DRY_RUN",
        }

        if action in ("", "NONE", "None") or severity == "OK":
            decision["status"] = "SKIPPED_NO_ACTION"
            decision["detail"] = "Alert requires no automated remediation."
            self._write_audit_entry(decision)
            return decision

        remaining_cooldown = self._check_cooldown(alert_id, current_ts)
        if remaining_cooldown is not None:
            decision["status"] = "SUPPRESSED_CIRCUIT_BREAKER"
            decision["detail"] = (
                f"Cooldown active for {alert_id}; retry in {remaining_cooldown}s."
            )
            self._write_audit_entry(decision)
            return decision

        if not self.execute:
            decision["status"] = "DRY_RUN_SIMULATED"
            decision["detail"] = (
                f"Would execute '{action}' per {runbook} (pass --execute to apply)."
            )
            self._write_audit_entry(decision)
            return decision

        outcome = self._perform_bounded_action(action, alert)
        self._record_execution(alert_id, current_ts)
        decision["status"] = "EXECUTED"
        decision["detail"] = outcome
        self._write_audit_entry(decision)
        return decision


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bounded SRE self-healing executor with circuit-breaker cooldowns."
    )
    parser.add_argument("--execute", action="store_true", help="Apply bounded remediation actions.")
    parser.add_argument("--cooldown-seconds", type=int, default=DEFAULT_COOLDOWN_SECONDS)
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE)
    parser.add_argument("--audit-log", default=DEFAULT_AUDIT_LOG)
    parser.add_argument("--artifact-dir", default=DEFAULT_ARTIFACT_DIR)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    healer = SelfHealer(
        execute=args.execute,
        cooldown_seconds=args.cooldown_seconds,
        state_file=args.state_file,
        audit_log=args.audit_log,
        artifact_dir=args.artifact_dir,
    )
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        alerts = payload if isinstance(payload, list) else [payload]
        for alert in alerts:
            if isinstance(alert, dict):
                print(json.dumps(healer.process_alert(alert), sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
