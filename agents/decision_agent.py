import json
import re
import math
from core.llm import ask_llm


class DecisionAgent:

    def decide(self, listings: list, product_query: str = "") -> list:
        if not listings:
            return []

        for l in listings:
            l["total_cost"] = l.get("price", 0) + l.get("shipping", 0)

        prices = [l["total_cost"] for l in listings if l.get("total_cost")]
        min_price = min(prices) if prices else 1
        max_price = max(prices) if prices else 1

        for l in listings:
            price   = l.get("total_cost") or max_price
            trust   = l.get("trust_score") or 0
            rating  = l.get("rating")
            r_count = l.get("rating_count") or 0

            # Price score: cheapest = 100
            if max_price == min_price:
                price_score = 100
            else:
                price_score = 100 - ((price - min_price) / (max_price - min_price) * 100)

            # Trust score: 0-10 → 0-100
            trust_score = trust * 10

            # Rating score: None = 50 neutral
            rating_score = (rating / 5.0) * 100 if rating else 50

            # Review count: log scale
            review_score = min(100, math.log10(r_count + 1) * 40) if r_count > 0 else 30

            # Weighted score
            # Price 40% — main factor
            # Trust 25%
            # Rating 20%
            # Reviews 15%
            final_score = (
                price_score  * 0.40 +
                trust_score  * 0.25 +
                rating_score * 0.20 +
                review_score * 0.15
            )

            l["price_score"]  = round(price_score, 1)
            l["rating_score"] = round(rating_score, 1)
            l["review_score"] = round(review_score, 1)
            l["final_score"]  = round(final_score, 1)

        # Sort: highest final_score first
        listings.sort(key=lambda x: -x.get("final_score", 0))

        # LLM explanation for top pick only
        best = listings[0]
        prompt = f"""User searched for: "{product_query}"

Best product found:
- Name: {best.get('name','')[:60]}
- Price: Rs.{best.get('price')}
- Platform: {best.get('source','')}
- Trust Score: {best.get('trust_score',0)}/10
- Rating: {best.get('rating','Not available')}
- Review Count: {best.get('rating_count','Unknown')}
- Final Score: {best.get('final_score',0)}/100

In 2 sentences tell user why this is the best deal.
Mention price, platform trustworthiness, and rating honestly.
If rating missing, say so. Plain text only."""

        try:
            reasoning = ask_llm(prompt, temperature=0.2, max_tokens=150)
            listings[0]["llm_reasoning"] = reasoning.strip()
        except Exception as e:
            print(f"[DecisionAgent] LLM failed: {e}")
            listings[0]["llm_reasoning"] = (
                f"Best deal at {best.get('source','')} for "
                f"Rs.{int(best.get('price',0))} "
                f"with trust score {best.get('trust_score',0)}/10 "
                f"and overall score {best.get('final_score',0)}/100."
            )

        return listings
# ```

# ---

# ## Scoring breakdown:

# | Factor | Weight | Reason |
# |---|---|---|
# | 💰 Price | **40%** | Sabse sasta — main priority |
# | 🛡️ Trust | 25% | Amazon/Flipkart reliable hai |
# | ⭐ Rating | 20% | Product quality |
# | 📊 Reviews | 15% | Kitne logon ne rate kiya |

# **Nike example mein ab:**
# ```
# ₹3,547 flipkart  → Price 100 + Trust 100 + Rating 50 + Review 30 = 76/100 ✅ BEST
# ₹4,497 amazon    → Price  85 + Trust 100 + Rating 50 + Review 30 = 70/100
# ₹9,746 flipkart  → Price  40 + Trust 100 + Rating 50 + Review 30 = 57/100