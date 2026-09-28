"""Reference implementation of the Optimism POC signal rules.

The same logic runs inside Clay as formula columns (see clay/formulas.md).
This module exists so that:
  * the keyword / seniority / exclusion rules can be unit-tested before they
    are pasted into Clay,
  * hit quality from 01 (LinkedIn job signal) and 03 (Google fallback) can be
    scored with one ruleset when comparing CSV exports offline.

Usage:
    python -m poc.signal_rules "Head of Stablecoin Partnerships"
    python -m poc.signal_rules --csv tables/01_net_new_entrant_signal.csv --title-col "Job Title"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "signal_config.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _term_regex(term: str) -> re.Pattern:
    # Whole-word match, case-insensitive, optional plural "s".
    # Word separators are "-", " " or nothing, so "on-chain", "on chain" and "onchain" all match.
    escaped = "[- ]?".join(re.escape(w) for w in re.split(r"[- ]", term.lower()))
    return re.compile(rf"(?<![a-z0-9]){escaped}s?(?![a-z0-9])", re.IGNORECASE)


@dataclass
class TitleMatch:
    triggered: bool
    priority: str  # "High" | "Medium" | ""
    keyword: str
    keyword_tier: str
    seniority: str
    reason: str


class SignalRules:
    def __init__(self, config: dict | None = None, include_suggested: bool = True):
        cfg = config or load_config()
        kws = [k for k in cfg["keywords"] if include_suggested or k["status"] == "customer"]
        # Longest first so "digital assets" wins over "digital asset".
        kws.sort(key=lambda k: -len(k["term"]))
        self.keywords = [(k["term"], k["tier"], _term_regex(k["term"])) for k in kws]

        sen = list(cfg["seniority"]["required"])
        if include_suggested:
            sen += cfg["seniority"]["suggested"]
        sen.sort(key=len, reverse=True)
        self.seniority = [(s, _term_regex(s)) for s in sen]

        self.negatives = [(n, _term_regex(n)) for n in cfg["negative_title_terms"]]

    def match_title(self, title: str | None) -> TitleMatch:
        t = (title or "").strip()
        if not t:
            return TitleMatch(False, "", "", "", "", "empty title")

        for term, rx in self.negatives:
            if rx.search(t):
                return TitleMatch(False, "", "", "", "", f"negative term: {term}")

        kw = next(((term, tier) for term, tier, rx in self.keywords if rx.search(t)), None)
        if not kw:
            return TitleMatch(False, "", "", "", "", "no niche keyword")

        sen = next((s for s, rx in self.seniority if rx.search(t)), None)
        if not sen:
            return TitleMatch(False, "", kw[0], kw[1], "", "keyword but no seniority")

        priority = "High" if kw[1] == "A" else "Medium"
        return TitleMatch(True, priority, kw[0], kw[1], sen, "keyword + seniority")


def normalize_domain(value: str | None) -> str:
    """Normalize a URL / domain / email to a bare registrable-ish domain for suppression matching."""
    v = (value or "").strip().lower()
    if not v:
        return ""
    if "@" in v and "/" not in v:
        v = v.split("@", 1)[1]
    if "://" not in v:
        v = "http://" + v
    host = urlparse(v).hostname or ""
    for prefix in ("www.", "www2.", "careers.", "jobs."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    return host


def suppression_reason(domain: str, lists: dict[str, set[str]]) -> str:
    """Return the name of the first suppression list containing this domain, or '' if eligible.

    Mirrors the 'Suppressed By' formula in Clay; pass lists in priority order,
    e.g. {"Target 150": {...}, "Event Attendees": {...}}.
    """
    d = normalize_domain(domain)
    if not d:
        return ""
    return next((name for name, domains in lists.items() if d in domains), "")


def load_domain_set(csv_path: Path, column: str = "Domain") -> set[str]:
    with open(csv_path, encoding="utf-8") as f:
        return {normalize_domain(r[column]) for r in csv.DictReader(f) if r.get(column)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("title", nargs="?", help="A single job title to test")
    ap.add_argument("--csv", type=Path, help="Score every row of a CSV export")
    ap.add_argument("--title-col", default="Job Title")
    ap.add_argument("--customer-only", action="store_true", help="Ignore keywords/seniority marked 'suggested'")
    args = ap.parse_args()

    rules = SignalRules(include_suggested=not args.customer_only)
    if args.title:
        print(json.dumps(asdict(rules.match_title(args.title)), indent=2))
    if args.csv:
        with open(args.csv, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        hits = 0
        for r in rows:
            m = rules.match_title(r.get(args.title_col))
            hits += m.triggered
            print(f"{'HIT ' if m.triggered else 'miss'} {m.priority:<6} {r.get(args.title_col, '')[:70]:<70} {m.reason}")
        print(f"\n{hits}/{len(rows)} rows trigger")


if __name__ == "__main__":
    main()
