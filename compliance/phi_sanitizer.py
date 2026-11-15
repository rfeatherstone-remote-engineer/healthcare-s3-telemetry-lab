#!/usr/bin/env python3
import json
import re
import sys

SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
MRN_PATTERN = re.compile(r"\bMRN-\d{6,10}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")

def scrub_text(text: str) -> str:
    text = SSN_PATTERN.sub("[REDACTED-SSN]", text)
    text = MRN_PATTERN.sub("[REDACTED-MRN]", text)
    text = EMAIL_PATTERN.sub("[REDACTED-PHI]", text)
    text = PHONE_PATTERN.sub("[REDACTED-PHI]", text)
    return text

def sanitize_record(record: dict) -> dict:
    sanitized = {}
    for key, value in record.items():
        if isinstance(value, str):
            sanitized[key] = scrub_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_record(value)
        else:
            sanitized[key] = value
    return sanitized

def main() -> None:
    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
            print(json.dumps(sanitize_record(data)), flush=True)
        except json.JSONDecodeError:
            print(scrub_text(raw), flush=True)

if __name__ == "__main__":
    main()
