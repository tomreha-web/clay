# HubSpot field mapping

Clay → HubSpot. strategicabm and Apollo read these properties downstream.
**Create the `clay_*` custom properties in HubSpot before the first live sync.** Group: "Clay Signals".

## Company object (match on `domain`)

| Clay column (table 05) | HubSpot property | Type | Notes |
|---|---|---|---|
| Domain (normalized) | `domain` | standard | Upsert key |
| Company Name | `name` | standard | Only set if empty in HubSpot |
| Employee Count | `numberofemployees` | standard | From Enrich Company |
| Industry | `industry` | standard | HubSpot uses fixed enum values, so map through a formula or leave off |
| HQ Country | `country` | standard | |
| LinkedIn URL | `linkedin_company_page` | standard | |
| clay_signal_component | `clay_signal_component` | dropdown | `01 – Net-New Entrant Signal` / `02 – Target 150 Monitor` / `03 – Google Fallback (experimental)` / `04 – Lookalike` |
| clay_signal_type | `clay_signal_type` | dropdown | `Net-new entrant – job posting`, `New hire in niche title`, `Job change`, `Promotion`, `Target job posting` |
| clay_signal_source | `clay_signal_source` | single-line text | LinkedIn Jobs / Google / Clay people data |
| clay_signal_priority | `clay_signal_priority` | dropdown | High (Tier A keyword) / Medium (Tier B) |
| clay_signal_matched_keyword | `clay_signal_matched_keyword` | single-line text | e.g. `stablecoin` |
| clay_signal_job_title | `clay_signal_job_title` | single-line text | e.g. `Head of Stablecoin` |
| clay_signal_job_url | `clay_signal_job_url` | single-line text (URL) | |
| clay_signal_detected_at | `clay_signal_detected_at` | date | Lets strategicabm trigger "new this week" plays |
| clay_net_new_entrant | `clay_net_new_entrant` | checkbox | TRUE only for 01/03 (not already a target) |

**Overwrite rule:** the `clay_signal_*` fields always show the **latest** signal. If OP wants
history, also create a HubSpot note or timeline event per signal. That's a v2 option.

## Contact object (01c triggered contacts, 02 tracked contacts)

| Clay column | HubSpot property | Type | Notes |
|---|---|---|---|
| First / Last Name | `firstname` / `lastname` | standard | |
| Title | `jobtitle` | standard | |
| LinkedIn URL | `clay_linkedin_url` | single-line text, **unique value** | Upsert key while there's no email |
| Persona | `clay_persona` | dropdown | Hiring exec / Adjacent leader / Exec sponsor |
| Company domain | association → Company | association | Associate to the company record from the same row |
| Email | `email` | standard | **Empty in v1. Apollo fills it.** |

⚠️ **Decision for OP:** HubSpot dedupes contacts on `email`. If Clay creates contacts without
email, it has to upsert on `clay_linkedin_url` (a unique-value property). Apollo then needs to
match on it too, or duplicates will appear. The alternative is running Clay's email waterfall
only on the ≤3 contacts per triggered company, which is cheap because it's gated.

## Stub vs. live
- **Stub (now):** formula F9 builds the JSON payload in table 05, and `Sync Status = STUB – not sent`.
- **Live:** replace F9 with the HubSpot actions, keeping the same mapping. No table restructure needed.
