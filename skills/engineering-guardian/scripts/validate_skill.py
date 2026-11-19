#!/usr/bin/env python3
"""Validate the portable Codex skill manifest and file structure (stdlib only)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED = [
    "SKILL.md", "agents/openai.yaml", "references/engineering.md",
    "references/review.md", "references/technology.md",
    "references/evolution.md", "scripts/check_repo.py", "scripts/review_diff.py",
]
FRONTMATTER = re.compile(r"\A---\s*\n(?P<header>.*?)\n---\s*\n", re.S)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    for rel in REQUIRED:
        file = root / rel
        if not file.is_file():
            errors.append(f"Missing required file: {rel}")
    skill = root / "SKILL.md"
    if skill.is_file():
        body = skill.read_text(encoding="utf-8")
        match = FRONTMATTER.search(body)
        if not match:
            errors.append("SKILL.md missing YAML frontmatter")
        else:
            pairs = {}
            for line in match.group("header").splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if ":" not in line:
                    errors.append(f"Malformed frontmatter: {line}")
                    continue
                key, value = line.split(":", 1)
                pairs[key.strip()] = value.strip()
            if set(pairs) != {"name", "description"}:
                errors.append("Frontmatter must have exactly 'name' and 'description'")
            if pairs.get("name") != "engineering-guardian":
                errors.append("Unexpected skill name")
            if len(pairs.get("description", "")) < 45:
                errors.append("Description is too vague to trigger reliably")
        for rel in set(re.findall(r"(?:references/[A-Za-z0-9_.-]+\.md|scripts/[A-Za-z0-9_.-]+\.py)", body)):
            if not (root / rel).is_file():
                errors.append(f"Broken local reference in SKILL.md: {rel}")
    for path in root.rglob("*"):
        if path.is_symlink():
            errors.append(f"Unsupported symlink: {path.relative_to(root)}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    for issue in errors:
        print(f"FAIL: {issue}")
    if errors:
        return 1
    print(f"PASS: Skill structure valid at {args.root.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
