# Credit efficiency

OP's concern is burning credits "trolling the ocean". The design has three rules.

1. **Suppress before anything paid.** Target 150 and event-attendee lookups are free lookups.
   They sit at the front of 01a, 03b and 04. A suppressed company is never monitored, enriched or pushed.
2. **Formulas are the gate.** `Eligible for Signal` (F3) controls what gets monitored.
   `Enrich Row?` (F5) controls every paid enrichment. Both are free formula columns.
3. **Enrich only triggered rows.** The sourced audience never gets enriched as a whole. Company
   enrichment and contact search run only on the ~few hundred weekly triggers, and never twice
   for the same company (F5 checks the HubSpot Sync Queue first).

The Google fallback is query-driven (60 searches a week, whatever the audience size), not
per-company. AI extraction and size checks run only on results that already pass the free title rule.

## Order of columns (paid ones marked 💳)

```
01a  Source(Find Companies, 1k+) → Domain(normalized) → Lookup Target150 → Lookup Events → Suppressed By → Eligible for Signal
01b  💳Signal: Job Postings (only Eligible rows) → Title Match → Signal Hit? → Lookup Already Pushed → Enrich Row?
     → 💳Enrich Company [if Enrich Row?] → 💳Find People ×3 [if Enrich Row?] → Write to 05 [if Enrich Row?]
03a  💳Google Search ×60/wk → Write to 03b
03b  Title Match → 💳AI Extract Company [if hit] → Lookups → 💳Enrich Company [if hit & !suppressed] → Found in 01?
05   💳HubSpot upsert [if Sync Status != Sent]
```

## Rough weekly volume (placeholder assumptions)

`python3 scripts/estimate_credits.py`, with a 9,000-company 1k+ audience, 1,650 suppressed, and a 3% weekly trigger rate:

| | Paid actions / week |
|---|---|
| Gated (this POC) | ~1,300 |
| Blanket enrichment of the audience | ~36,000 (and again on every refresh) |

These counts are **paid actions**, not credits. Pass the workspace's current per-action costs
with `--company-cost`, `--person-cost`, `--google-cost` and `--ai-cost`. The audience size and
trigger rate are guesses until the first run. **Check them after week 1.**
