# Live validation: Clay data pull, 2026-09-28

Pulled from the Clay GTM workspace through the Clay connector, to test the signal logic on real
data before building tables. These are **people and company records, not job postings.** The
connector can't query job postings, so the job-posting rows in `tables/01b` are illustrative.

## 1. Company search: 1k+ employees, "stablecoin" in company description

`select from companies where employee_count >= 1000 and description contains ("stablecoin")` returned 6:

| Company | Employees | Industry | What it shows |
|---|---|---|---|
| Coinbase | 7,019 | Financial Services | Crypto-native. **Should be suppressed** (event list) |
| Circle | 1,533 | Financial Services | Crypto-native. **Should be suppressed** |
| Corpay | 7,263 | Financial Services | Legacy B2B payments now talking about "emerging stablecoin payment rails". **Net-new entrant profile** |
| MoneyGram | 3,333 | Financial Services | Remittance company supporting "fiat and stablecoin transactions". **Net-new entrant profile** |
| Banco Bisa | 1,593 | Banking | Bolivian bank |
| Eco | 1,548 (size bucket says 11–50) | Internet | **Bad data:** headcount and size bucket disagree. Reason to gate on a verified headcount after enrichment |

Takeaway: companies that describe themselves as stablecoin players are *already public* about it.
The POC's edge is catching companies **before** the description changes. That's why 01 is driven
by job postings, not firmographics.

## 2. People search: niche keywords in LinkedIn headline, at 10 large non-crypto companies

Companies: Apple, Visa, Mastercard, JPMorganChase, Walmart, Amazon, PayPal, Shopify, Citi, Stripe.
Query: headline contains a niche keyword AND a seniority term, ≤3 per company.

**True positives (title passes `poc/signal_rules.py`):**

| Person | Title | Company | Role start |
|---|---|---|---|
| Frida V. | Director Visa Stablecoins – Latin America/Caribbean Region | Visa | **2026-08** ← ≤90-day niche hire |
| Oliver Silvey | Vice President, Blockchain & Digital Assets | Mastercard | 2025-12 |
| Christian Rau | SVP Global Partnerships Digital Assets, Blockchain and Fintech Enablement | Mastercard | 2025-01 |
| Antônia Souza | Director, Head of Blockchain & Cryptocurrencies, LAC | Visa | 2025-01 |
| Biser Dimitrov | Global Head Digital Assets Technology | Citi | 2024-09 |
| Ryan Rugg | Global Head of Digital Assets TTS | Citi | 2022-08 |
| Subramaniam Vaithiyalingam | Director – Blockchain, Crypto, and Digital Currencies | PayPal | 2024-01 |

**False positives (headline matched, title doesn't):** Amazon "Pathways Operations Manager",
JPMorganChase "Corporate Investment Banking – Analyst", Amazon "Director, Corporate Business Development",
Shopify "Business Development Manager", and others.

Takeaways that shaped the build:
1. **Match on title, not headline or description.** Headline matching produced roughly 1 false positive for every 2 true positives. Title + seniority rules remove all of them (see `tests/test_signal_rules.py::test_headline_noise_does_not_trigger_on_title`).
2. **Component 02 works on current data.** Visa's August 2026 stablecoin director hire is exactly the "new hire in niche title" signal. In the sample, Visa and Mastercard sit in the Target 150 placeholder.
3. No Apple hits came back at the people level. That fits the thesis: a company that's just entering the space has a **job posting**, not yet a person in the seat. Detecting that is 01's job.

Clay task IDs (for reference): `mcp-task_0tm2yufCembdoyGAUKd` (companies), `mcp-task_0tm2ywr8YASJ7vASFPY` (people).
