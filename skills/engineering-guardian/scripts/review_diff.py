#!/usr/bin/env python3
"""Summarize change scope and paths requiring enhanced human review."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROTECTED = (".github/workflows/", "AGENTS.md", "SKILL.md", "skills/engineering-guardian/SKILL.md",
             "skills/engineering-guardian/scripts/", "maintenance/sources.json")
HIGH_RISK_TOKENS = ("auth", "payment", "migration", "permission", "secret", "billing", "token", "security")


def rank_files(files: list[str]) -> list[dict]:
    results = []
    for name in files:
        normalized = name.replace("\\", "/")
        reason = []
        severity = "LOW"
        if any(normalized == p or normalized.startswith(p) for p in PROTECTED):
            severity, reason = "HIGH", ["protected engineering/security policy or workflow"]
        if any(token in normalized.lower() for token in HIGH_RISK_TOKENS):
            severity = "HIGH"
            reason.append("sensitive domain inferred from path; check manually")
        if normalized.endswith((".sql", ".tf", ".tfvars")):
            severity = "HIGH"
            reason.append("schema/infrastructure changes can cause external side effects")
        results.append({"file": normalized, "risk": severity, "reason": reason or ["normal code change; review based on actual behavior"]})
    return results


def changed_paths(repo: Path, base: str, head: str) -> list[str]:
    args = ["git", "-C", str(repo), "diff", "--name-only", "--diff-filter=ACMRD", f"{base}...{head}"]
    completed = subprocess.run(args, capture_output=True, text=True, check=False, timeout=25)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git diff failed")
    return sorted(x for x in completed.stdout.splitlines() if x)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--base", default="HEAD~1", help="Existing git base reference")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()
    try:
        paths = changed_paths(args.repo, args.base, args.head)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc), "verified": False}, ensure_ascii=False))
        return 3
    print(json.dumps({"verified": True, "base": args.base, "head": args.head,
                      "changed_file_count": len(paths), "paths": rank_files(paths),
                      "notice": "Path-based triage only; read the actual diff for correctness/security."},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
