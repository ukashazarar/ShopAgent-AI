from urllib.parse import urlparse
from config import TRUSTED_DOMAINS


class TrustAgent:
    """
    Evaluates trust score (0-10) for each listing based on:
    - Known trusted domain registry (config.py)
    - HTTPS usage
    - Domain structure (subdomain spam detection)
    Does NOT filter out untrusted — assigns score and flags.
    Orchestrator decides whether to filter.
    """

    def evaluate(self, listings: list) -> list:
        for listing in listings:
            link = listing.get("link", "")
            score = 0
            is_trusted = False

            try:
                parsed = urlparse(link)
                domain = parsed.netloc.lower()

                # Remove www.
                clean_domain = domain.replace("www.", "")

                # 1. HTTPS check (+1)
                if parsed.scheme == "https":
                    score += 1

                # 2. Known trusted domain registry
                for trusted, trust_val in TRUSTED_DOMAINS.items():
                    if trusted in clean_domain:
                        score += trust_val
                        is_trusted = True
                        break

                # 3. Penalize suspicious patterns
                if clean_domain.count(".") > 2:
                    score -= 1  # too many subdomains

                if any(x in clean_domain for x in ["deal", "cheap", "best-price", "offer"]):
                    score -= 1  # suspicious keyword domains

                score = max(0, min(10, score))

            except Exception:
                score = 0

            listing["trust_score"] = score
            listing["is_trusted"] = is_trusted

        # Sort: trusted first, then by trust score descending
        listings.sort(key=lambda x: (-x.get("trust_score", 0)))

        trusted_count = sum(1 for l in listings if l.get("is_trusted"))
        print(f"[TrustAgent] {trusted_count}/{len(listings)} listings from trusted domains.")

        return listings
