"""Check that the Clay JS formula F4 (clay/formulas.md) agrees with poc/signal_rules.py.

Pulls the F4 code block out of the markdown, swaps {{Job Title}} for each test title,
runs it with node, and compares hit/priority with the Python rules.

    python3 scripts/check_formula_parity.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from poc.signal_rules import SignalRules  # noqa: E402

TITLES = [
    "Head of Stablecoin", "Director Visa Stablecoins- Latin America/Caribbean Region",
    "Vice President, Blockchain & Digital Assets", "Global Head Digital Assets Technology",
    "Director, Head of Blockchain & Cryptocurrencies, LAC", "Pathways Operations Manager",
    "Blockchain Engineer", "VP, Tokenization", "Director of On-Chain Settlement",
    "Director of On Chain Settlement", "Head of DLT Strategy", "SVP Tokenized Deposits",
    "Head of Crypto Fraud Investigations", "Head of Cryptography", "Director, Middleton Office",
    "Lead, Distributed Ledger Technology", "Director, Settlement Infrastructure", "",
]


def main() -> int:
    md = (ROOT / "clay" / "formulas.md").read_text(encoding="utf-8")
    block = re.search(r"## F4 .*?```js\n(.*?)```", md, re.S).group(1)
    js = (f"const f = (JOB) => {block.replace('{{Job Title}}', 'JOB').strip()};\n"
          f"console.log(JSON.stringify({json.dumps(TITLES)}.map(f)));")
    proc = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    if proc.returncode:
        print(proc.stderr)
        return 1
    res = json.loads(proc.stdout)

    rules, bad = SignalRules(), 0
    for title, j in zip(TITLES, res):
        p = rules.match_title(title)
        ok = (p.triggered, p.priority) == (j["hit"], j["priority"])
        bad += not ok
        print(f"{'ok ' if ok else 'DIFF'} py={p.triggered!s:<5} {p.priority:<6} js={j['hit']!s:<5} {j['priority']:<6} {title}")
    print(f"\n{len(TITLES) - bad}/{len(TITLES)} match")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
