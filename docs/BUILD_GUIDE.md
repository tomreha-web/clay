# Build guide: Optimism POC in Clay

**Workbook:** `Optimism POC – Signal Detection`
**Scope in v1:** find signals and identify companies and people, then push to HubSpot.
**Out of scope:** messaging, sequencing, and email enrichment. Apollo does those.

Build the tables in the order below. Each one depends on the tables above it.

| # | Table | Purpose | Paid actions? |
|---|---|---|---|
| 00a | `00a – Config: Signal Keywords` | Keyword list the customer signs off on | No |
| 00b | `00b – Target 150 (master)` | The 150 accounts. Used to **suppress** in 01 and 03 and as the **base** for 02 | No |
| 00c | `00c – Suppression: Event Attendees` | 1–2k accounts already in the space | No |
| 01a | `01a – Net-New Entrant Audience (1k+)` | Sourced companies, gated by suppression | Sourcing only |
| 01b | `01 – Net-New Entrant Signal` ⭐ | Weekly job posting signal. **The demo moment** | Only on triggered rows |
| 01c | `01c – Triggered Contacts` | 2–3 people per triggered company | Only on triggered rows |
| 02  | `02 – Target 150 Monitor` | Job changes, promotions, niche new hires at the 150 | Signal runs only |
| 03a/b | `03 – Google Fallback (experimental)` | Postings that don't show up on LinkedIn | ~60 searches/week |
| 04  | `04 – Lookalike Expansion (bonus)` | Lookalikes of the 150, fed into 01a | One-off |
| 05  | `05 – HubSpot Sync Queue` | One place where all pushes are deduped and mapped | HubSpot actions only |

Import CSVs for each table are in `tables/`. Formulas referenced as **F1–F9** are in `clay/formulas.md`.

---

## 00 · Inputs and suppression (build these first)

> ⚠️ **Why first:** OP doesn't want to burn credits "trolling the ocean". Suppression is a free
> lookup and sits **before** every paid column, so a suppressed company never costs a credit.

### 00a – Config: Signal Keywords
- Import `tables/00a_config_signal_keywords.csv`.
- **Table description:**
  `TODO (customer): confirm final ~20 keyword/title terms. Rows with Status=suggested were added by Clay and need sign-off. After changes, update the KW list in formula F4 in 01b and 03b.`

### 00b – Target 150 (master)
- Import `tables/00b_target_150_master.csv`. The 5 rows are **samples**.
- Add formula column `Domain (normalized)` (F1).
- **Table description:**
  `TODO (customer): replace the 5 sample rows with OP's ~150 target accounts (Company Name, Domain, HubSpot owner, tier). Sample rows have Is Sample = TRUE. Delete them once the real list is in. This table is the suppression list for 01/03 and the base for 02.`
- Later: sync this table from a HubSpot list (e.g. "OP Target Accounts") so it stays current without manual edits.

### 00c – Suppression: Event Attendees
- Import `tables/00c_suppression_event_attendees.csv`. The 6 rows are **samples**.
- Add `Domain (normalized)` (F1).
- **Table description:**
  `TODO (customer): upload the ~1,000–2,000 event-attendee accounts that are already in the space. Only a Domain column is needed; names are optional. Add a column per event if you want to know which list suppressed a company.`

---

## 01 · Net-New Entrant Signal (primary)

### 01a – Net-New Entrant Audience (1k+)
1. **Source → Find Companies** (Clay company search)
   - Employee count: **1,001+** (size ranges 1,001–5,000 / 5,001–10,000 / 10,001+).
   - **No industry filter.** Leave it off on purpose (see "Tightening levers" below).
   - Optional: HQ country = US / UK / EU / SG / HK if OP sells only in certain regions. Not set in v1.
2. Columns, in this order:
   1. `Domain (normalized)` (F1)
   2. `Lookup · Target 150`: *Lookup Single Row in Other Table* → `00b`, on `Domain (normalized)`
   3. `Lookup · Event Attendees`: same lookup → `00c`
   4. `Suppressed By` (F2)
   5. `Eligible for Signal` (F3). **Master gate.**
3. **5k+ variant:** add a view `5k+ comparison` filtered on `Employee Count ≥ 5000`. It uses the
   same rows, so it costs nothing extra. For a side-by-side trigger count, filter 01b by the same
   field. If the team wants two fully separate signal runs, duplicate 01b and point its signal
   at the 5k+ view.
4. **Table description:**
   `Audience = companies with 1k+ employees, no industry filter (v1). Suppressed = Target 150 + event attendees. Only rows with Eligible for Signal = TRUE are monitored. View '5k+ comparison' is the tighter variant. TODO: refresh the source monthly so new 1k+ companies get picked up.`

### 01b – 01 – Net-New Entrant Signal ⭐
1. **Source → Signals → Job Postings** (monitor companies from `01a`)
   - Monitor: `01a`, **view filtered to `Eligible for Signal = TRUE`**. Suppressed companies are never monitored.
   - Job title keywords: the Tier A and Tier B terms from `00a` (placeholder list).
   - **Schedule: Weekly, Monday.** Change it in the signal settings. Keep formula F6's lookback in step with it.
2. Formula columns (all free):
   `Title Match` (F4) → `Signal Hit?`, `Signal Priority`, `Matched Keyword` → `Posted Within Lookback` (F6)
   → `Lookup · Already Pushed` (on `05`) → `Enrich Row?` (F5).
3. Paid columns, **all with run condition `{{Enrich Row?}}`**:
   - **Enrich Company**: headcount, industry, HQ, revenue range, LinkedIn URL. Light only.
   - **Find People at Company** → writes to `01c` (see below).
   - **Write to Table → `05 – HubSpot Sync Queue`**.
4. **Table description:**
   `Weekly job-posting signal on the 1k+ audience. A row triggers when the title has a niche keyword AND a seniority term (Head/Director/VP/Lead) AND no negative term. Paid enrichment only runs when Enrich Row? = TRUE. TODO (customer): confirm the keyword list (00a).`

**What the demo shows:** filter to `Signal Hit? = TRUE`. Apple "Head of Stablecoin" is at the top,
posted this week, never on anyone's list. Then show the Visa and Coinbase rows: they matched,
but suppression stopped them before any credit was spent.

### 01c – Triggered Contacts
- Source: **Find People at Company**, triggered from `01b` (run condition `Enrich Row?`). Limit **3 per company**.
- Persona filters, in priority order:
  1. **Hiring exec.** Use the job posting's hiring manager / poster field when the signal returns one. If not, search for the posting's title family one level up (e.g. "Head of Digital Assets", "SVP Payments").
  2. **Adjacent leader.** Titles: Head of Payments, Treasurer, Head of Treasury, Head of Digital, Head of Innovation, Head of Emerging Payments.
  3. **Exec sponsor.** CFO, CTO, Chief Digital Officer, President (Financial Services).
- Columns: Full Name, Title, LinkedIn URL, Persona, Company Domain.
- **No email waterfall in v1.** Apollo enriches downstream. (Open item: turn on Clay email for these ≤3 people if OP wants HubSpot contacts to dedupe on email. See `docs/hubspot-field-mapping.md`.)
- Write to `05` (contact section).

### Tightening levers (document for OP, don't turn on in v1)
| Lever | When to use | Effect |
|---|---|---|
| Industry filter on 01a | If weekly triggers are over ~300 | Cuts retail-crypto noise. Risks missing "Apple-type" surprises |
| Tier A only | If Tier B (blockchain / crypto / web3) is noisy | Keeps institutional-intent terms only |
| 5k+ view | If the team wants only the biggest logos | Fewer, bigger triggers |
| Drop the `lead` seniority | If "Lead Engineer"-style roles slip through | Keeps only Head/Director/VP titles |

---

## 02 · Target 150 Monitor

1. **Company-level signals** on `00b – Target 150 (master)`:
   - **Signals → New Hires**, with title filter = the niche keyword list (00a) plus seniority. Weekly.
   - **Signals → Job Postings**, same keyword list. Weekly. (A target posting "Head of Stablecoin" is a strong buying signal.)
2. **Contacts table `02a – Target 150 Contacts`**: import `tables/02a_target150_contacts.csv`.
   Then Find People at each of the 150 using the persona filters in 01c. Those contacts are the tracked champions.
   - **Signals → Job Changes**: tracked contact moves company. The *new* company goes to `01a`
     and runs through suppression, so a champion landing at a net-new entrant shows up in 01.
   - **Signals → Promotions**: tracked contact promoted (e.g. Director → MD Digital Assets).
3. Every signal writes a row to `02b – Target 150 Signal Log` and then to `05`.
4. **Table description:**
   `Out-of-the-box monitor for OP's 150 target accounts: job changes, promotions, new hires and job postings in niche titles. Weekly. TODO (customer): replace sample accounts in 00b. Contacts start from sample rows (real people from Clay data, 2026-09-28).`

Live proof already in the sample (from Clay data, not made up): **Visa hired a "Director Visa
Stablecoins – Latin America/Caribbean Region" who started 2026-08**. That's a ≤90-day niche new
hire at a target account.

---

## 03 · Google Fallback (experimental)

> 🧪 **EXPERIMENTAL.** Put the label in the table name and description. The goal is to measure
> whether Google finds postings that LinkedIn misses (career pages, ATS boards, Glassdoor; US pay
> transparency rules mean many of these are public) and how early it finds them.

**Design: query-driven, not audience-driven.** Running Google per company over the whole audience
would mean blanket enrichment. Instead, each row is one `site × title pattern` query:
6 sites × 10 patterns = **60 searches per week, whatever the audience size.**

### 03a – Google Query Matrix
- Import `tables/03a_google_query_matrix.csv` (60 rows, generated from config).
- Column **Google Search** (Clay native / Serper), input `Google Query` (F7),
  time filter **past week** (`qdr:w`), 10 results. Run condition: `{{Active}}`.
- Schedule: weekly, same day as 01b.
- **Write to Table → `03b`**, one row per organic result.

### 03b – Google Results
Columns, in order. Paid steps are marked 💳.
1. `Result Title`, `Result URL`, `Snippet` (from the write)
2. `Title Match` (F4 on `Result Title`), then `Title Match Hit?`. Free.
3. 💳 `Extracted Company`: AI / Claygent, *only if `Title Match Hit?`*.
   Prompt: "From this job posting URL, title and snippet, return the hiring company's name and website domain. Return null for recruiting agencies."
4. `Domain (normalized)` (F1), then suppression lookups on 00b/00c, then `Suppressed By` (F2). Free.
5. 💳 `Enrich Company` (size check), *only if hit and not suppressed*. Then `Passes Size (≥1k)`.
6. `Lookup · 01 Match` on `01b`, then `Found in 01?` and `Days Ahead of 01` (F8). Free.
7. `Net-New vs 01` = hit AND passes size AND NOT found in 01. **This is the number that matters.**
8. Only rows with `Net-New vs 01` go on to contacts and `05`, tagged `clay_signal_source = Google Fallback`.

### How to compare 03 and 01 (after 3–4 weekly runs)
| Metric | Formula |
|---|---|
| Precision | qualified hits (pass size + title) ÷ total results |
| Incremental coverage | `Net-New vs 01` count ÷ 01 trigger count |
| Lead time | median `Days Ahead of 01` where both found the posting |
| Cost per incremental account | 03 credits ÷ `Net-New vs 01` count |

Rule for moving off experimental: keep 03 if it adds **≥10% incremental coverage** or a
**median lead time of ≥3 days**. Otherwise retire it.

---

## 04 · Lookalike Expansion (bonus)

- Source: **Find Lookalike Companies**, seeded from `00b – Target 150` domains (top 5–10 lookalikes per seed).
- Then F1, suppression lookups, F2, and `Add to 01 Audience?` = not suppressed AND employees ≥ 1k.
- **Write to Table → `01a`** for rows where `Add to 01 Audience?` is TRUE. Lookalikes then get
  the weekly signal monitoring with no enrichment spend until they trigger.
- Table description: `Bonus: lookalikes of the Target 150. They feed the 01 audience instead of going straight to HubSpot. TODO: re-run when the real 150 list lands.`

---

## 05 · HubSpot Sync Queue

Every component writes here. One table means one field mapping, one dedupe point, and one place
to swap the stub for the live integration.

- Columns: see `tables/05_hubspot_sync_queue.csv` and `docs/hubspot-field-mapping.md`.
- **Dedupe:** use `Domain (normalized)` as the row key. Enable "Write to Table → update existing row if match".
- **While HubSpot isn't connected:** `HubSpot Company Payload (stub)` (F9) shows the exact JSON. `Sync Status = STUB – not sent`.
- **When it's connected:** add **HubSpot → Create or Update Company** (match on `domain`), then **Create or Update Contact** for the 01c contacts, associated to the company. Run condition: `Sync Status != "Sent"`. Write the returned HubSpot ID back.
- strategicabm picks up the new `clay_*` properties from HubSpot for orchestration. Clay doesn't message anyone.
