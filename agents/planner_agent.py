import json
import re
from urllib.parse import urlparse, unquote
from core.llm import ask_llm

NON_PRODUCT_PATTERNS = [
    r"^are you",
    r"^what is",
    r"^who is",
    r"^how to",
    r"^why\b",
    r"^when\b",
    r"^can you",
    r"^do you",
    r"^is this",
    r"^hello\b",
    r"^hi\b",
    r"^test$",
    r"^hey\b",
]

CAPTCHA_PHRASES = [
    "are you a human", "are you human", "robot", "captcha",
    "verify", "access denied", "just a moment", "checking your browser",
    "please wait", "enable javascript", "ddos protection"
]


def extract_product_from_url_slug(url: str) -> str:
    """Extract product name directly from URL path — reliable for Flipkart/Amazon."""
    try:
        path = urlparse(url).path
        parts = [p for p in path.split("/") if p and len(p) > 10
                 and not p.startswith("dp")
                 and not p.startswith("p")
                 and not p.startswith("itm")
                 and not p.startswith("B0")]
        if parts:
            slug = parts[0]
            name = unquote(slug).replace("-", " ").replace("_", " ").strip()
            # Remove noise words
            for noise in ["buy", "online", "best", "price", "india", "low"]:
                name = re.sub(rf'\b{noise}\b', '', name, flags=re.IGNORECASE)
            name = " ".join(name.split())
            return name[:100] if len(name) > 5 else ""
    except Exception:
        pass
    return ""


class PlannerAgent:

    def create_plan(self, user_input: str) -> dict:
        cleaned = user_input.strip().lower()

        # Reject non-product questions
        for pattern in NON_PRODUCT_PATTERNS:
            if re.match(pattern, cleaned, re.IGNORECASE):
                return {
                    "input_type": "invalid",
                    "product_query": "",
                    "category": "unknown",
                    "priority_platforms": [],
                    "search_strategy": "invalid input",
                    "original_input": user_input,
                    "error": f"'{user_input}' does not look like a product. Try: 'Samsung Galaxy S24' or 'Nike Air Max'."
                }

        # Too short
        if len(cleaned) < 3:
            return {
                "input_type": "invalid",
                "product_query": "",
                "category": "unknown",
                "priority_platforms": [],
                "search_strategy": "invalid input",
                "original_input": user_input,
                "error": "Input too short. Please enter a valid product name."
            }

        is_url = user_input.startswith("http")

        # For URLs — extract product name from slug directly (no scraping needed)
        url_product = ""
        if is_url:
            url_product = extract_product_from_url_slug(user_input)

        prompt = f"""You are a smart shopping assistant planner.

User input: "{user_input}"

Is this a valid product search? 
Valid: "iPhone 15 Pro", "Nike Air Max", "Samsung TV 55 inch", any product URL
Invalid: "Are you human?", "Hello", "What is AI", "Test"

Respond ONLY with valid JSON, no extra text:
{{
  "is_valid": true,
  "input_type": "url" or "product_name",
  "product_query": "clean search query for this product",
  "category": "electronics/clothing/footwear/appliances/books/general",
  "priority_platforms": ["amazon.in", "flipkart.com", "croma.com"],
  "search_strategy": "one line description",
  "error": ""
}}"""

        try:
            response = ask_llm(prompt, temperature=0.1)
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                plan = json.loads(match.group())
                plan["original_input"] = user_input

                if not plan.get("is_valid", True):
                    plan["input_type"] = "invalid"
                    plan["error"] = f"'{user_input}' does not look like a product name."
                    return plan

                # For URLs: prefer slug-extracted name over LLM guess
                if is_url and url_product:
                    plan["product_query"] = url_product
                    plan["input_type"] = "url"

                return plan

        except Exception as e:
            print(f"[PlannerAgent] LLM failed: {e}, using fallback")

        # Fallback
        return {
            "is_valid": True,
            "input_type": "url" if is_url else "product_name",
            "product_query": url_product if is_url and url_product else user_input,
            "category": "general",
            "priority_platforms": ["amazon.in", "flipkart.com", "croma.com"],
            "search_strategy": "general search",
            "original_input": user_input
        }