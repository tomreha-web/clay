"""Weekly paid-action estimate: gated design vs. blanket enrichment.

Counts *paid actions*. Multiply by the current per-action credit cost in the workspace
(pricing changes, so costs are flags here rather than hard-coded).

    python3 scripts/estimate_credits.py --audience 9000 --trigger-rate 0.03
    python3 scripts/estimate_credits.py --audience 9000 --company-cost 1 --person-cost 1 --google-cost 1 --ai-cost 1
"""

import argparse


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audience", type=int, default=9000, help="1k+ companies sourced into 01a (placeholder)")
    ap.add_argument("--suppressed", type=int, default=1650, help="Target 150 + event attendees that overlap the audience")
    ap.add_argument("--trigger-rate", type=float, default=0.03, help="Share of monitored companies with a qualifying posting per week")
    ap.add_argument("--contacts", type=int, default=3)
    ap.add_argument("--google-queries", type=int, default=60)
    ap.add_argument("--google-hit-rate", type=float, default=0.3, help="Share of Google results that pass the title rule")
    ap.add_argument("--company-cost", type=float, default=1.0)
    ap.add_argument("--person-cost", type=float, default=1.0)
    ap.add_argument("--google-cost", type=float, default=1.0)
    ap.add_argument("--ai-cost", type=float, default=1.0)
    a = ap.parse_args()

    monitored = max(a.audience - a.suppressed, 0)
    triggered = round(monitored * a.trigger_rate)
    g_results = a.google_queries * 10
    g_hits = round(g_results * a.google_hit_rate)

    gated = {
        "01 company enrich (triggered only)": triggered * a.company_cost,
        "01 find contacts (triggered only)": triggered * a.contacts * a.person_cost,
        "03 google searches": a.google_queries * a.google_cost,
        "03 AI company extraction (title hits only)": g_hits * a.ai_cost,
        "03 company enrich (title hits only)": g_hits * a.company_cost,
    }
    blanket = {
        "company enrich on whole audience": a.audience * a.company_cost,
        "find contacts on whole audience": a.audience * a.contacts * a.person_cost,
    }

    print(f"Audience {a.audience:,} | suppressed before paid steps {a.suppressed:,} | monitored {monitored:,}")
    print(f"Weekly triggers ≈ {triggered:,} ({a.trigger_rate:.0%})\n")
    print("GATED (this POC)")
    for k, v in gated.items():
        print(f"  {k:<45} {v:>10,.0f}")
    g_total = sum(gated.values())
    print(f"  {'TOTAL / week':<45} {g_total:>10,.0f}\n")
    print("BLANKET (what we're avoiding)")
    for k, v in blanket.items():
        print(f"  {k:<45} {v:>10,.0f}")
    b_total = sum(blanket.values())
    print(f"  {'TOTAL (and again on every refresh)':<45} {b_total:>10,.0f}\n")
    print(f"Gated design uses {g_total / b_total:.1%} of blanket enrichment.")
    print("Signal-monitoring costs are left out (same in both designs). Check them against the workspace's current pricing.")


if __name__ == "__main__":
    main()
