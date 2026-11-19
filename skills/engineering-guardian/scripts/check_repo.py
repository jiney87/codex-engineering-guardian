#!/usr/bin/env python3
"""Lightweight heuristic repository risk screen; never a security guarantee."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "dist", "build", "coverage",
    ".next", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".sh"}
MAX_BYTES = 800_000
TOKEN = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|sk-[A-Za-z0-9_-]{25,})")
SECRET_ASSIGNMENT = re.compile(
    r"\b(?:api[_-]?key|access[_-]?token|secret|password|private[_-]?key)\b\s*[:=]\s*[\"']([^\"']{8,})[\"']",
    re.I,
)
DANGEROUS_PY = re.compile(r"\b(?:os\.system|eval|exec)\s*\(")
SHELL_TRUE = re.compile(r"\bshell\s*=\s*True\b")


def screen_line(line: str, filename: str, lineno: int) -> list[dict]:
    """Produce findings. Static-only patterns deliberately favor precision."""
    out = []
    stripped = line.strip()
    # Intentional demo fixtures must be clearly marked, never production code.
    if "guardian: fixture" in line and "/tests/" in filename.replace("\\", "/"):
        return out
    m = TOKEN.search(line)
    if m:
        out.append({"severity": "BLOCKER", "rule": "possible-secret-token", "file": filename,
                    "line": lineno, "message": "Possible credential embedded in source; revoke if real."})
    m = SECRET_ASSIGNMENT.search(line)
    if m and not re.search(r"(example|dummy|placeholder|your[_-]|changeme|test[_-])", m.group(1), re.I):
        out.append({"severity": "HIGH", "rule": "hardcoded-credential", "file": filename,
                    "line": lineno, "message": "Suspicious literal credential assignment; verify manually."})
    if filename.endswith(".py") and not stripped.startswith("#"):
        if DANGEROUS_PY.search(line) and not stripped.startswith(("DANGEROUS_PY", "#")):
            out.append({"severity": "HIGH", "rule": "dynamic-execution", "file": filename,
                        "line": lineno, "message": "Dynamic execution; check tainted inputs and alternatives."})
        if SHELL_TRUE.search(line) and not stripped.startswith(("SHELL_TRUE", "#")):
            out.append({"severity": "HIGH", "rule": "shell-execution", "file": filename,
                        "line": lineno, "message": "Shell execution enabled; inspect tainted data flow."})
    return out


def audit(root: Path) -> dict:
    root = root.resolve()
    issues: list[dict] = []
    stats = {"scanned_files": 0, "skipped_large": 0, "skipped_unreadable": 0}
    if not root.is_dir():
        return {"error": f"Not a directory: {root}", "issues": [], "stats": stats}
    for dirname, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS and not (Path(dirname) / d).is_symlink())
        for basename in sorted(files):
            file = Path(dirname) / basename
            if file.suffix.lower() not in EXTENSIONS or file.is_symlink():
                continue
            try:
                if file.stat().st_size > MAX_BYTES:
                    stats["skipped_large"] += 1
                    continue
                lines = file.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError):
                stats["skipped_unreadable"] += 1
                continue
            stats["scanned_files"] += 1
            rel = str(file.relative_to(root)).replace("\\", "/")
            for n, line in enumerate(lines, 1):
                issues.extend(screen_line(line, rel, n))
    counts = {s: sum(i["severity"] == s for i in issues) for s in ("BLOCKER", "HIGH", "MEDIUM", "LOW")}
    return {"root": str(root), "issues": issues, "counts": counts,
            "stats": stats, "limitations": "Heuristic static scan: false positives and false negatives are possible."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path.cwd())
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--fail-on", choices=("none", "blocker", "high"), default="high")
    args = ap.parse_args()
    result = audit(args.root)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Scanned {result['stats']['scanned_files']} source files")
        for item in result["issues"]:
            print(f"{item['severity']} {item['file']}:{item['line']} {item['rule']}: {item['message']}")
        print(result["limitations"] if "limitations" in result else result.get("error", ""))
    if "error" in result:
        return 3
    if args.fail_on == "none":
        return 0
    return int(any(i["severity"] == "BLOCKER" or
                   (args.fail_on == "high" and i["severity"] == "HIGH")
                   for i in result["issues"]))


if __name__ == "__main__":
    sys.exit(main())
