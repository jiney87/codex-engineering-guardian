#!/usr/bin/env python3
"""Compare fingerprints of allowlisted public standards; never apply policy changes."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import date, timezone, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ALLOW_HOSTS = {"developers.openai.com", "docs.github.com", "owasp.org"}
LIMIT_BYTES = 500_000


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def normalize_text(raw_html: bytes) -> str:
    parser = TextExtractor()
    parser.feed(raw_html.decode("utf-8", errors="replace"))
    return " ".join(html.unescape(" ".join(parser.parts)).split())[:180_000]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_is_safe(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOW_HOSTS and not parsed.username and not parsed.password


def fetch(url: str) -> str:
    if not source_is_safe(url):
        raise ValueError(f"Source not on approved HTTPS host allowlist: {url}")
    request = Request(url, headers={"User-Agent": "EngineeringGuardian-StandardsWatch/0.1", "Accept": "text/html"})
    with urlopen(request, timeout=18) as response:
        final = response.geturl()
        if not source_is_safe(final):
            raise ValueError("Redirect left the approved HTTPS hosts")
        content = response.read(LIMIT_BYTES + 1)
    if len(content) > LIMIT_BYTES:
        raise ValueError("Page exceeds size limit")
    content_text = normalize_text(content)
    if len(content_text) < 150:
        raise ValueError("Insufficient extractable text")
    return content_text


def validate_registry(registry: dict, lock: dict) -> list[str]:
    issues: list[str] = []
    if registry.get("schema") != 1 or not isinstance(registry.get("sources"), list):
        issues.append("Invalid source registry schema")
    ids: set[str] = set()
    for source in registry.get("sources", []):
        if not isinstance(source, dict):
            issues.append("Malformed source entry")
            continue
        sid = source.get("id", "")
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,55}", sid):
            issues.append(f"Invalid source ID: {sid}")
        if sid in ids:
            issues.append(f"Duplicate source ID: {sid}")
        ids.add(sid)
        if not source_is_safe(source.get("url", "")):
            issues.append(f"Untrusted URL: {source.get('url')}")
    if lock.get("schema") != 1 or not isinstance(lock.get("sources"), dict):
        issues.append("Invalid lock schema")
    for sid, data in lock.get("sources", {}).items():
        if sid not in ids:
            issues.append(f"Unknown locked source: {sid}")
        if not re.fullmatch(r"[a-f0-9]{64}", data.get("sha256", "")):
            issues.append(f"Invalid lock digest for {sid}")
    return issues


def update_snapshots(registry: dict, lock: dict, getter=fetch, today: str | None = None) -> tuple[dict, list[dict]]:
    now = today or date.today().isoformat()
    new_lock = json.loads(json.dumps(lock))
    changed = []
    for source in registry["sources"]:
        sid, url = source["id"], source["url"]
        try:
            text = getter(url)
            current_hash = digest(text)
            old_hash = lock["sources"].get(sid, {}).get("sha256")
            if old_hash != current_hash:
                changed.append({"id": sid, "topic": source["topic"], "url": url,
                                "old_sha256": old_hash, "new_sha256": current_hash, "status": "baseline" if not old_hash else "changed"})
                new_lock["sources"][sid] = {"url": url, "sha256": current_hash, "observed_on": now}
        except Exception as exc:  # Report network errors, do not overwrite a valid baseline.
            changed.append({"id": sid, "url": url, "status": "unavailable", "error": type(exc).__name__})
    return new_lock, changed


def render_report(changes: list[dict], when: str) -> str:
    lines = ["# Standards watch / 官方规范变化观察", "", f"Observed: {when}", "",
             "**A page fingerprint change is not evidence of a policy change.** Review official upstream content before editing accepted rules.", ""]
    for item in changes:
        if item["status"] == "unavailable":
            lines.append(f"- UNAVAILABLE `{item['id']}`: fetch failed ({item['error']}); previous known fingerprint retained")
        else:
            lines.append(f"- {item['status'].upper()} `{item['id']}`: {item['url']} — inspect changes before proposing a rule")
    if not changes:
        lines.append("No fingerprint changes.")
    lines += ["", "Security: fetched content was treated as data and was not executed or used to modify policy.", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Validate local registry and lock without network")
    group.add_argument("--update", action="store_true", help="Fetch allowlisted sources and write changed fingerprint metadata")
    args = ap.parse_args()
    registry_path = ROOT / "maintenance/sources.json"
    lock_path = ROOT / "maintenance/sources.lock.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    issues = validate_registry(registry, lock)
    if issues:
        for issue in issues:
            print("ERROR:", issue)
        return 1
    if args.check:
        print(f"PASS: {len(registry['sources'])} approved sources, {len(lock['sources'])} recorded fingerprints")
        return 0
    new_lock, changes = update_snapshots(registry, lock)
    meaningful = [i for i in changes if i["status"] in {"baseline", "changed"}]
    if meaningful:
        lock_path.write_text(json.dumps(new_lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (ROOT / "maintenance/standards-watch.md").write_text(render_report(changes, datetime.now(timezone.utc).date().isoformat()), encoding="utf-8")
    print(json.dumps({"changed_or_baselined": len(meaningful), "unavailable": sum(i['status'] == 'unavailable' for i in changes), "changes": changes}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
