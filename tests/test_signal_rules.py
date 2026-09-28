import unittest

from poc.signal_rules import SignalRules, normalize_domain, suppression_reason


class TitleMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = SignalRules()
        cls.customer_only = SignalRules(include_suggested=False)

    def assertHit(self, title, priority=None, rules=None):
        m = (rules or self.rules).match_title(title)
        self.assertTrue(m.triggered, f"expected hit: {title!r} ({m.reason})")
        if priority:
            self.assertEqual(m.priority, priority, title)

    def assertMiss(self, title, rules=None):
        m = (rules or self.rules).match_title(title)
        self.assertFalse(m.triggered, f"expected miss: {title!r} ({m.keyword}/{m.seniority})")

    def test_demo_moment(self):
        self.assertHit("Head of Stablecoin", "High")

    def test_real_titles_from_live_sample(self):
        # Pulled from Clay people search on 2026-09-28 (validation/live_sample_2026-09-28.md)
        self.assertHit("Director Visa Stablecoins- Latin America/Caribbean Region", "High")
        self.assertHit("Vice President, Blockchain & Digital Assets", "High")
        self.assertHit("Global Head Digital Assets Technology", "High")
        self.assertHit("Director, Head of Blockchain & Cryptocurrencies, LAC", "Medium")
        self.assertHit("Director - Blockchain, Crypto, and Digital Currencies")

    def test_headline_noise_does_not_trigger_on_title(self):
        # These people matched on LinkedIn *headline* in the live sample; their titles don't qualify.
        self.assertMiss("Pathways Operations Manager")
        self.assertMiss("Corporate Investment Banking - Analyst")
        self.assertMiss("Director, Corporate Business Development")

    def test_keyword_needs_seniority(self):
        self.assertMiss("Blockchain Engineer")
        self.assertMiss("Stablecoin Operations Analyst")

    def test_seniority_variants(self):
        for t in ("VP, Tokenization", "Lead, Distributed Ledger Technology",
                  "Director of On-Chain Settlement", "Head of Onchain Products",
                  "Head of DLT Strategy", "Director, Settlement Infrastructure"):
            self.assertHit(t, "High")

    def test_suggested_terms_can_be_switched_off(self):
        self.assertHit("SVP Tokenized Deposits", rules=self.rules)
        self.assertMiss("SVP Tokenized Deposits", rules=self.customer_only)

    def test_negatives(self):
        self.assertMiss("Head of Crypto Fraud Investigations")
        self.assertMiss("Technical Recruiter, Web3 & Blockchain Lead")
        self.assertMiss("Digital Assets Strategy Intern")

    def test_word_boundaries(self):
        self.assertMiss("Head of Cryptography")          # not "crypto"
        self.assertMiss("Director, Middleton Office")    # "dlt" inside a word


class DomainTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_domain("https://www.Apple.com/careers"), "apple.com")
        self.assertEqual(normalize_domain("jobs.apple.com"), "apple.com")
        self.assertEqual(normalize_domain("tim@apple.com"), "apple.com")
        self.assertEqual(normalize_domain(""), "")

    def test_suppression_order(self):
        lists = {"Target 150": {"visa.com"}, "Event Attendees": {"visa.com", "coinbase.com"}}
        self.assertEqual(suppression_reason("www.visa.com", lists), "Target 150")
        self.assertEqual(suppression_reason("coinbase.com", lists), "Event Attendees")
        self.assertEqual(suppression_reason("apple.com", lists), "")


if __name__ == "__main__":
    unittest.main()
