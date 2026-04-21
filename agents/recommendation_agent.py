from core.llm import ask_llm


class RecommendationAgent:
    """
    Uses Groq LLM to generate a natural language recommendation
    explaining WHY this is the best deal.
    """

    def recommend(self, listings: list, product_query: str = "") -> dict:
        if not listings:
            return {}

        best = listings[0]

        # Build context about alternatives
        alternatives = []
        for l in listings[1:4]:
            if l.get("price"):
                alternatives.append(
                    f"{l.get('source','unknown')} at ₹{l.get('price','?')} "
                    f"(trust: {l.get('trust_score',0)}/10, rating: {l.get('rating','N/A')})"
                )

        alt_text = "; ".join(alternatives) if alternatives else "no alternatives found"

        prompt = f"""You are a helpful shopping assistant.

The user searched for: "{product_query}"

Best option found:
- Product: {best.get('name', 'N/A')}
- Price: ₹{best.get('price', 'N/A')}
- Platform: {best.get('source', 'N/A')}
- Trust Score: {best.get('trust_score', 0)}/10
- Rating: {best.get('rating', 'Not available')}
- Trusted Platform: {"Yes" if best.get('is_trusted') else "No"}

Other options: {alt_text}

Write a SHORT (2-3 sentences) friendly recommendation explaining:
1. Why this is the best deal
2. One thing to watch out for (if any)

Be concise and helpful. No markdown, plain text only."""

        try:
            explanation = ask_llm(prompt, temperature=0.4)
            best["recommendation_text"] = explanation.strip()
        except Exception as e:
            print(f"[RecommendationAgent] LLM failed: {e}")
            trust_str = f"trust score {best.get('trust_score', 0)}/10"
            rating_str = f"rated {best.get('rating')}/5" if best.get("rating") else "no rating available"
            best["recommendation_text"] = (
                f"Best deal found at {best.get('source', 'this platform')} "
                f"for ₹{best.get('price', 'N/A')} ({trust_str}, {rating_str})."
            )

        return best
