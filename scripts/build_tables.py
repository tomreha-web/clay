"""Generate the importable CSVs in tables/ from config + sample rows.

    python3 scripts/build_tables.py

Every table has an `Is Sample` column. Rows marked TRUE are placeholders for the demo
and should be deleted once the real lists arrive. Sample rows come from two places:
  * LIVE: pulled from Clay search on 2026-09-28 (see validation/live_sample_2026-09-28.md)
  * ILLUSTRATIVE: made up to show the flow. The job postings are not real.
The `Sample Source` column says which.
"""

import csv
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from poc.signal_rules import SignalRules, normalize_domain, suppression_reason  # noqa: E402

CFG = json.loads((ROOT / "config" / "signal_config.json").read_text())
OUT = ROOT / "tables"
RULES = SignalRules()
TODAY = "2026-09-28"


def write(name, rows):
    OUT.mkdir(exist_ok=True)
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote tables/{name} ({len(rows)} rows)")


# ---------------------------------------------------------------- 00 · Config / suppression
write("00a_config_signal_keywords.csv", [
    {"Term": k["term"], "Tier": k["tier"], "Status": k["status"],
     "Confirmed by Customer": "FALSE", "Notes": "" if k["status"] == "customer" else "Clay suggestion to reach ~20 terms"}
    for k in CFG["keywords"]
])

TARGET_150 = [
    # (name, domain, owner, tier) — SAMPLE placeholders until OP sends the real list
    ("JPMorganChase", "jpmorganchase.com", "TBD", "Tier 1"),
    ("Citi", "citigroup.com", "TBD", "Tier 1"),
    ("Visa", "visa.com", "TBD", "Tier 1"),
    ("Mastercard", "mastercard.com", "TBD", "Tier 1"),
    ("Stripe", "stripe.com", "TBD", "Tier 2"),
]
write("00b_target_150_master.csv", [
    {"Company Name": n, "Domain": d, "Domain (normalized)": normalize_domain(d),
     "Account Owner (HubSpot)": o, "Tier": t, "HubSpot Company ID": "",
     "Is Sample": "TRUE", "Sample Source": "ILLUSTRATIVE placeholder"}
    for n, d, o, t in TARGET_150
])

EVENT_ATTENDEES = [
    ("Coinbase", "coinbase.com", "Sample event 2026"),
    ("Circle", "circle.com", "Sample event 2026"),
    ("Kraken", "kraken.com", "Sample event 2026"),
    ("Anchorage Digital", "anchorage.com", "Sample event 2026"),
    ("Paxos", "paxos.com", "Sample event 2026"),
    ("Fireblocks", "fireblocks.com", "Sample event 2026"),
]
write("00c_suppression_event_attendees.csv", [
    {"Company Name": n, "Domain": d, "Domain (normalized)": normalize_domain(d),
     "Event": e, "Is Sample": "TRUE", "Sample Source": "ILLUSTRATIVE placeholder"}
    for n, d, e in EVENT_ATTENDEES
])

SUPPRESSION = {
    "Target 150": {normalize_domain(d) for _, d, _, _ in TARGET_150},
    "Event Attendees": {normalize_domain(d) for _, d, _ in EVENT_ATTENDEES},
}

# ---------------------------------------------------------------- 01a · Audience
AUDIENCE = [
    # (name, domain, employees, industry, country, source)
    ("Apple", "apple.com", 220429, "Computers and Electronics Manufacturing", "United States", "LIVE"),
    ("Walmart", "walmart.com", 2100000, "Retail", "United States", "ILLUSTRATIVE"),
    ("Amazon", "amazon.com", 1500000, "Software Development", "United States", "ILLUSTRATIVE"),
    ("Corpay", "corpay.com", 7263, "Financial Services", "United States", "LIVE"),
    ("MoneyGram", "moneygram.com", 3333, "Financial Services", "United States", "LIVE"),
    ("Banco Bisa", "bisa.com", 1593, "Banking", "Bolivia", "LIVE"),
    ("Visa", "visa.com", 30000, "Financial Services", "United States", "ILLUSTRATIVE"),
    ("Coinbase", "coinbase.com", 7019, "Financial Services", "United States", "LIVE"),
    ("Circle", "circle.com", 1533, "Financial Services", "United States", "LIVE"),
    ("Shopify", "shopify.com", 8100, "Software Development", "Canada", "ILLUSTRATIVE"),
    ("Mid-size Example Co", "example-midsize.com", 640, "Financial Services", "United States", "ILLUSTRATIVE"),
]
audience_rows = []
for n, d, emp, ind, ctry, src in AUDIENCE:
    nd = normalize_domain(d)
    sup = suppression_reason(nd, SUPPRESSION)
    audience_rows.append({
        "Company Name": n, "Domain": d, "Employee Count": emp, "Industry": ind, "Country": ctry,
        "Domain (normalized)": nd,
        "Lookup · Target 150": nd if sup == "Target 150" else "",
        "Lookup · Event Attendees": nd if sup == "Event Attendees" else "",
        "Suppressed By": sup,
        "Eligible for Signal": str(not sup and emp >= CFG["audience"]["primary_min_employees"]).upper(),
        "In 5k+ View": str(emp >= CFG["audience"]["comparison_min_employees"]).upper(),
        "Is Sample": "TRUE",
        "Sample Source": "LIVE (Clay company search 2026-09-28)" if src == "LIVE" else "ILLUSTRATIVE",
    })
write("01a_audience_1k_plus.csv", audience_rows)
eligible = {r["Domain (normalized)"]: r for r in audience_rows}

# ---------------------------------------------------------------- 01b · Net-New Entrant Signal
POSTINGS = [
    # (domain, title, posted, url) — ILLUSTRATIVE postings, not real listings
    ("apple.com", "Head of Stablecoin", "2026-09-22", "https://jobs.apple.com/en-us/details/SAMPLE-0001"),
    ("walmart.com", "Director, Digital Assets & Tokenization", "2026-09-24", "https://careers.walmart.com/SAMPLE-0002"),
    ("corpay.com", "VP, Stablecoin Payments", "2026-09-23", "https://www.linkedin.com/jobs/view/SAMPLE-0003"),
    ("moneygram.com", "Head of On-Chain Settlement", "2026-09-21", "https://www.linkedin.com/jobs/view/SAMPLE-0004"),
    ("bisa.com", "Lead, Blockchain Strategy", "2026-09-25", "https://www.linkedin.com/jobs/view/SAMPLE-0005"),
    ("amazon.com", "Blockchain Engineer", "2026-09-22", "https://www.amazon.jobs/SAMPLE-0006"),
    ("shopify.com", "Crypto Payments Intern", "2026-09-23", "https://www.linkedin.com/jobs/view/SAMPLE-0007"),
    ("visa.com", "Director, Stablecoin Settlement", "2026-09-24", "https://www.linkedin.com/jobs/view/SAMPLE-0008"),
    ("coinbase.com", "Head of Institutional Stablecoins", "2026-09-22", "https://www.linkedin.com/jobs/view/SAMPLE-0009"),
]
signal_rows = []
for d, title, posted, url in POSTINGS:
    a = eligible[d]
    m = RULES.match_title(title)
    elig = a["Eligible for Signal"] == "TRUE"
    enrich = elig and m.triggered
    signal_rows.append({
        "Company Name": a["Company Name"], "Domain (normalized)": d, "Employee Count": a["Employee Count"],
        "Job Title": title, "Job Posted Date": posted, "Job URL": url,
        "Signal Source": "LinkedIn Jobs (Clay Job Postings signal)",
        "Signal Detected At": TODAY,
        "Suppressed By": a["Suppressed By"], "Eligible for Signal": a["Eligible for Signal"],
        "Signal Hit?": str(m.triggered).upper(), "Signal Priority": m.priority,
        "Matched Keyword": m.keyword, "Matched Seniority": m.seniority, "Match Reason": m.reason,
        "Enrich Row?": str(enrich).upper(),
        "Company Enrichment": "run" if enrich else "skipped (0 credits)",
        "Find Contacts (2–3)": "run" if enrich else "skipped (0 credits)",
        "HubSpot Push Status": "STUB – queued in 05" if enrich else "",
        "Is Sample": "TRUE", "Sample Source": "ILLUSTRATIVE posting (not a real listing)",
    })
write("01b_net_new_entrant_signal.csv", signal_rows)

# ---------------------------------------------------------------- 01c · Contacts on triggered rows
CONTACT_PERSONAS = [
    ("Hiring exec (job poster / hiring manager)", "From job posting 'hiring team' field; fall back to title search"),
    ("Adjacent leader: payments / treasury / digital", "Head of Payments, Treasurer, Head of Digital, Head of Innovation"),
    ("Exec sponsor", "CFO, CTO, Chief Digital Officer, President of Financial Services"),
]
write("01c_triggered_contacts.csv", [
    {"Company Name": r["Company Name"], "Domain (normalized)": r["Domain (normalized)"],
     "Persona": p, "Search Logic": logic, "Full Name": "", "Title": "", "LinkedIn URL": "",
     "Email": "(Apollo enriches downstream – not in Clay v1)",
     "Is Sample": "TRUE", "Sample Source": "STRUCTURE ONLY – populated when Find People runs"}
    for r in signal_rows if r["Enrich Row?"] == "TRUE" for p, logic in CONTACT_PERSONAS
])

# ---------------------------------------------------------------- 02 · Target 150 Monitor
LIVE_CONTACTS = [
    # Real people from Clay people search 2026-09-28, at sample Target 150 accounts.
    ("Frida V.", "Director Visa Stablecoins- Latin America/Caribbean Region", "Visa", "visa.com", "2026-08", "https://www.linkedin.com/in/fridavargas/"),
    ("Oliver Silvey", "Vice President, Blockchain & Digital Assets", "Mastercard", "mastercard.com", "2025-12", "https://www.linkedin.com/in/oliver-silvey/"),
    ("Biser Dimitrov", "Global Head Digital Assets Technology", "Citi", "citigroup.com", "2024-09", "https://www.linkedin.com/in/biserdimitrov/"),
    ("Ryan Rugg", "Global Head of Digital Assets TTS", "Citi", "citigroup.com", "2022-08", "https://www.linkedin.com/in/ryanrugg/"),
    ("Christian Rau", "Senior Vice President Global Partnerships Digital Assets, Blockchain and Fintech Enablement", "Mastercard", "mastercard.com", "2025-01", "https://www.linkedin.com/in/christian-rau-5a01b22/"),
    ("Sonu Sahu", "Corporate Investment Banking - Analyst", "JPMorganChase", "jpmorganchase.com", "2026-01", "https://www.linkedin.com/in/sahusonu/"),
]


def months_since(ym: str) -> int:
    y, m = map(int, ym.split("-"))
    ty, tm = map(int, TODAY.split("-")[:2])
    return (ty - y) * 12 + (tm - m)


target_contacts = []
for name, title, co, d, start, url in LIVE_CONTACTS:
    m = RULES.match_title(title)
    recent = months_since(start) <= 3
    sig = "New hire in niche title" if (m.triggered and recent) else ""
    target_contacts.append({
        "Full Name": name, "Title": title, "Company Name": co, "Domain (normalized)": d,
        "LinkedIn URL": url, "Current Role Start": start,
        "Niche Title?": str(m.triggered).upper(), "Signal Priority": m.priority,
        "Started ≤ 90 days": str(recent).upper(), "Target 150 Signal": sig,
        "Is Sample": "TRUE", "Sample Source": "LIVE (Clay people search 2026-09-28)",
    })
write("02a_target150_contacts.csv", target_contacts)

write("02b_target150_signal_log.csv", [
    {"Detected At": TODAY, "Signal Type": "New hire in niche title", "Company Name": "Visa",
     "Domain (normalized)": "visa.com", "Person": "Frida V.",
     "Detail": "Director Visa Stablecoins – LAC, started 2026-08", "Source": "Clay people data",
     "Pushed to HubSpot": "STUB", "Is Sample": "TRUE", "Sample Source": "LIVE (Clay people search 2026-09-28)"},
    {"Detected At": TODAY, "Signal Type": "Job change (champion left)", "Company Name": "Mastercard",
     "Domain (normalized)": "mastercard.com", "Person": "(example)",
     "Detail": "Tracked contact moved to a new company – new company goes to 01 audience check",
     "Source": "Clay Job Change signal", "Pushed to HubSpot": "STUB", "Is Sample": "TRUE", "Sample Source": "ILLUSTRATIVE"},
    {"Detected At": TODAY, "Signal Type": "Promotion", "Company Name": "Citi",
     "Domain (normalized)": "citigroup.com", "Person": "(example)",
     "Detail": "Director → MD, Digital Assets", "Source": "Clay Promotion signal",
     "Pushed to HubSpot": "STUB", "Is Sample": "TRUE", "Sample Source": "ILLUSTRATIVE"},
])

# ---------------------------------------------------------------- 03 · Google fallback
gf = CFG["google_fallback"]
matrix = []
for i, (site, pat) in enumerate(itertools.product(gf["sites"], gf["title_patterns"]), 1):
    site_op = f"site:{site}" if "." in site else f"inurl:{site}"
    matrix.append({
        "Query ID": f"Q{i:03d}", "Site": site, "Title Pattern": pat,
        "Google Query": f"{site_op} {pat} -intern -recruiter",
        "Date Restrict": gf["date_restrict"], "Results per Query": gf["results_per_query"],
        "Active": "TRUE", "Is Sample": "FALSE", "Sample Source": "Generated from config/signal_config.json",
    })
write("03a_google_query_matrix.csv", matrix)

GOOGLE_RESULTS = [
    # (query_id_site, title, url, extracted_company, domain, employees, in_01, days_ahead)
    ("boards.greenhouse.io", "Head of Stablecoin Partnerships", "https://boards.greenhouse.io/SAMPLE/jobs/1", "Example Retailer Inc", "example-retailer.com", 12000, False, None),
    ("myworkdayjobs.com", "Director, Digital Assets & Tokenization", "https://walmart.wd5.myworkdayjobs.com/SAMPLE", "Walmart", "walmart.com", 2100000, True, 3),
    ("glassdoor.com/job-listing", "Head of Stablecoin", "https://www.glassdoor.com/job-listing/SAMPLE", "Apple", "apple.com", 220429, True, 0),
    ("jobs.lever.co", "Lead, Stablecoin Operations", "https://jobs.lever.co/SAMPLE/2", "Small Fintech LLC", "example-smallfintech.com", 85, False, None),
]
write("03b_google_results.csv", [
    {"Detected At": TODAY, "Site": s, "Result Title": t, "Result URL": u,
     "Extracted Company": c, "Domain (normalized)": d, "Employee Count": e,
     "Title Match Hit?": str(RULES.match_title(t).triggered).upper(),
     "Signal Priority": RULES.match_title(t).priority,
     "Passes Size (≥1k)": str(e >= 1000).upper(),
     "Suppressed By": suppression_reason(d, SUPPRESSION),
     "Found in 01?": str(in01).upper(), "Days Ahead of 01": "" if ahead is None else ahead,
     "Net-New vs 01": str((not in01) and e >= 1000 and RULES.match_title(t).triggered).upper(),
     "Is Sample": "TRUE", "Sample Source": "ILLUSTRATIVE"}
    for s, t, u, c, d, e, in01, ahead in GOOGLE_RESULTS
])

# ---------------------------------------------------------------- 04 · Lookalike expansion
write("04_lookalike_expansion.csv", [
    {"Seed Account (from Target 150)": seed, "Lookalike Company": n, "Domain (normalized)": d,
     "Similarity Score": sc, "Employee Count": e,
     "Suppressed By": suppression_reason(d, SUPPRESSION),
     "Add to 01 Audience?": str(e >= 1000 and not suppression_reason(d, SUPPRESSION)).upper(),
     "Is Sample": "TRUE", "Sample Source": "ILLUSTRATIVE"}
    for seed, n, d, sc, e in [
        ("visa.com", "Mastercard", "mastercard.com", 0.94, 33000),
        ("visa.com", "Example Card Network", "example-cardnetwork.com", 0.81, 4200),
        ("citigroup.com", "Example Global Bank", "example-globalbank.com", 0.88, 90000),
        ("stripe.com", "Example Payments Co", "example-payments.com", 0.79, 2500),
    ]
])

# ---------------------------------------------------------------- 05 · HubSpot sync queue
queue = []
for r in signal_rows:
    if r["Enrich Row?"] != "TRUE":
        continue
    queue.append({
        "Domain (normalized)": r["Domain (normalized)"], "Company Name": r["Company Name"],
        "numberofemployees": r["Employee Count"],
        "clay_signal_component": "01 – Net-New Entrant Signal",
        "clay_signal_type": "Net-new entrant – job posting",
        "clay_signal_source": r["Signal Source"], "clay_signal_priority": r["Signal Priority"],
        "clay_signal_matched_keyword": r["Matched Keyword"], "clay_signal_job_title": r["Job Title"],
        "clay_signal_job_url": r["Job URL"], "clay_signal_detected_at": r["Signal Detected At"],
        "clay_net_new_entrant": "TRUE", "HubSpot Company ID": "", "Sync Status": "STUB – not sent",
        "Is Sample": "TRUE", "Sample Source": "Derived from 01b sample rows",
    })
queue.append({**queue[0], "Domain (normalized)": "visa.com", "Company Name": "Visa", "numberofemployees": 30000,
              "clay_signal_component": "02 – Target 150 Monitor", "clay_signal_type": "New hire in niche title",
              "clay_signal_source": "Clay people data", "clay_signal_priority": "High",
              "clay_signal_matched_keyword": "stablecoin",
              "clay_signal_job_title": "Director Visa Stablecoins- Latin America/Caribbean Region",
              "clay_signal_job_url": "", "clay_net_new_entrant": "FALSE",
              "Sample Source": "LIVE (Clay people search 2026-09-28)"})
write("05_hubspot_sync_queue.csv", queue)
