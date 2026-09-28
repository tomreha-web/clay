# Clay formula columns (copy-paste)

Clay formula columns take JavaScript expressions. `{{Column Name}}` is the Clay column token:
type `/` in the formula editor and pick the column, then paste the rest.
All formula and lookup columns cost **0 credits**. That's why every gate below is a formula.

The keyword lists match `config/signal_config.json`. If you change one, change the other, then run
`python3 -m unittest` to make sure the rules still pass.

---

## F1 · `Domain (normalized)`
Used in every table that joins to a suppression list.

```js
(() => {
  let v = String({{Domain}} || "").trim().toLowerCase();
  if (!v) return "";
  if (v.includes("@") && !v.includes("/")) v = v.split("@")[1];
  v = v.replace(/^https?:\/\//, "").split("/")[0].split("?")[0];
  return v.replace(/^(www2?|careers|jobs)\./, "");
})()
```

## F2 · `Suppressed By`
Put it after the two **Lookup Single Row in Other Table** columns:
- `Lookup · Target 150` looks up table `00b – Suppression: Target 150`, matching `Domain (normalized)`.
- `Lookup · Event Attendees` looks up table `00c – Suppression: Event Attendees`, matching `Domain (normalized)`.
- Optional: `Lookup · HubSpot Open Deal`, a HubSpot "Lookup Company" set to *only run if* the domain isn't empty. Leave it off in v1 (see docs/credit-efficiency.md).

```js
{{Lookup · Target 150}}?.["Domain (normalized)"] ? "Target 150"
: {{Lookup · Event Attendees}}?.["Domain (normalized)"] ? "Event Attendees"
: ""
```

## F3 · `Eligible for Signal` (**the master gate**)
Every paid column downstream uses **Run condition: `{{Eligible for Signal}}`**.

```js
!{{Suppressed By}} && Number({{Employee Count}} || 0) >= 1000
```

For the 5k+ comparison view, filter on `{{Employee Count}} >= 5000`. You don't need a second table.

## F4 · `Title Match` (keyword + seniority + negatives)
Returns an object. The next columns read its fields.

```js
(() => {
  const t = String({{Job Title}} || "");
  const rx = (term) => new RegExp("(?<![a-z0-9])" +
      term.toLowerCase().split(/[- ]/).map(w => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("[- ]?") +
      "s?(?![a-z0-9])", "i");

  // PLACEHOLDER: customer to confirm (~20 terms). Tier A = institutional intent, B = broad.
  const KW = [
    ["settlement infrastructure","A"],["distributed ledger","A"],["tokenized deposits","A"],
    ["programmable money","A"],["real-world assets","A"],["tokenized assets","A"],
    ["digital currency","B"],["digital assets","A"],["cryptocurrency","B"],["digital asset","A"],
    ["tokenization","A"],["tokenisation","A"],["stablecoins","A"],["stablecoin","A"],
    ["blockchain","B"],["on-chain","A"],["onchain","A"],["layer 2","B"],["crypto","B"],
    ["web3","B"],["dlt","A"]
  ];
  const SEN = ["managing director","general manager","vice president","global head",
               "director","chief","head","lead","svp","evp","vp"];
  const NEG = ["anti-money laundering investigator","talent acquisition","sales development",
               "customer support","internship","recruiter","cashier","intern","teller","fraud"];

  const neg = NEG.find(n => rx(n).test(t));
  if (!t || neg) return { hit: false, priority: "", keyword: "", seniority: "", reason: neg ? "negative: " + neg : "empty" };
  const kw = KW.find(([k]) => rx(k).test(t));
  if (!kw) return { hit: false, priority: "", keyword: "", seniority: "", reason: "no keyword" };
  const sen = SEN.find(s => rx(s).test(t));
  if (!sen) return { hit: false, priority: "", keyword: kw[0], seniority: "", reason: "no seniority" };
  return { hit: true, priority: kw[1] === "A" ? "High" : "Medium", keyword: kw[0], seniority: sen, reason: "keyword + seniority" };
})()
```

Then add three small formula columns:
- `Signal Hit?` → `{{Title Match}}?.hit === true`
- `Signal Priority` → `{{Title Match}}?.priority`
- `Matched Keyword` → `{{Title Match}}?.keyword`

## F5 · `Enrich Row?` (**the paid-enrichment gate**)
Every enrichment in the Output Layer uses **Run condition: `{{Enrich Row?}}`**.

```js
{{Eligible for Signal}} && {{Signal Hit?}} && !{{Already Pushed to HubSpot}}
```

`Already Pushed to HubSpot` is a Lookup Single Row on `05 – HubSpot Sync Queue` by
`Domain (normalized)`. That way a company that triggers again next week isn't enriched twice.

## F6 · `Posted Within Lookback`
```js
(() => {
  const d = new Date({{Job Posted Date}});
  return !isNaN(d) && (Date.now() - d.getTime()) / 864e5 <= 7; // 7 = weekly cadence; match config.cadence.lookback_days
})()
```

## F7 · `Google Query` (03 – Google Fallback)
Row = one site × title-pattern pair from `03a – Google Query Matrix`.

```js
`site:${{{Site}}} ${{{Title Pattern}}} -intern -recruiter`
```

## F8 · `Found in 01?` / `Days Ahead of 01` (03 comparison)
`Lookup · 01 Match` is a Lookup Single Row on `01b – Net-New Entrant Signal`, matching `Domain (normalized)`.

```js
!!{{Lookup · 01 Match}}?.["Domain (normalized)"]
```
```js
{{Lookup · 01 Match}}?.["Signal Detected At"]
  ? Math.round((new Date({{Lookup · 01 Match}}["Signal Detected At"]) - new Date({{Detected At}})) / 864e5)
  : null   // positive = Google found it N days before LinkedIn did
```

## F9 · `HubSpot Company Payload (stub)`
While the HubSpot connection isn't live, this column **is** the sync. It shows exactly what would be sent.
When HubSpot is connected, swap it for the native **HubSpot → Create or Update Company** action,
using the same field mapping (docs/04-output-layer-hubspot.md).

```js
JSON.stringify({
  domain: {{Domain (normalized)}},
  name: {{Company Name}},
  numberofemployees: {{Employee Count}},
  industry: {{Industry}},
  clay_signal_type: {{Signal Type}},
  clay_signal_source: {{Signal Source}},
  clay_signal_priority: {{Signal Priority}},
  clay_signal_matched_keyword: {{Matched Keyword}},
  clay_signal_job_title: {{Job Title}},
  clay_signal_job_url: {{Job URL}},
  clay_signal_detected_at: {{Signal Detected At}},
  clay_net_new_entrant: true
}, null, 2)
```
