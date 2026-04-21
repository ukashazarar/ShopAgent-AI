from agents.planner_agent import PlannerAgent, extract_product_from_url_slug, CAPTCHA_PHRASES
from agents.product_agent import ProductAgent
from agents.search_agent import SearchAgent
from agents.collection_agent import CollectionAgent
from agents.trust_agent import TrustAgent
from agents.decision_agent import DecisionAgent
from agents.recommendation_agent import RecommendationAgent
from urllib.parse import urlparse


class AgentOrchestrator:

    def run(self, user_input: str, min_price: float = 50.0, max_results: int = 20):

        planner          = PlannerAgent()
        product_agent    = ProductAgent()
        search_agent     = SearchAgent()
        collection_agent = CollectionAgent()
        trust_agent      = TrustAgent()
        decision_agent   = DecisionAgent()
        rec_agent        = RecommendationAgent()

        # ── Step 1: Plan ──────────────────────────────────────────────────────
        print("[Orchestrator] Step 1: Planning...")
        plan = planner.create_plan(user_input)
        print(f"[Orchestrator] Plan: {plan}")

        if plan.get("input_type") == "invalid":
            error_msg = plan.get("error", "Invalid input. Please enter a product name.")
            return error_msg, [], None

        # ── Step 2: Extract product name ──────────────────────────────────────
        print("[Orchestrator] Step 2: Extracting product...")

        if plan["input_type"] == "url":
            # Try 1: URL slug — fast, no CAPTCHA risk
            product_name = extract_product_from_url_slug(user_input)
            print(f"[Orchestrator] Slug extracted: '{product_name}'")

            # Try 2: scrape page — only if slug gave nothing
            if not product_name:
                scraped = product_agent.extract_product(user_input)
                captcha_words = ["are you", "human", "robot", "captcha",
                                 "verify", "access denied", "just a moment"]
                is_captcha = any(w in (scraped or "").lower() for w in captcha_words)
                if scraped and scraped != "Unknown Product" and not is_captcha:
                    product_name = scraped
                    print(f"[Orchestrator] Scraped: '{product_name}'")

            # Try 3: LLM plan query
            if not product_name:
                product_name = plan.get("product_query", "")
                print(f"[Orchestrator] From LLM plan: '{product_name}'")

            # Final fallback
            if not product_name:
                product_name = user_input

            plan["product_query"] = product_name

        else:
            # Product name input — LLM already cleaned it in planner
            product_name = plan.get("product_query", user_input)

        print(f"[Orchestrator] Product: {product_name}")

        # ── Step 3: Search ────────────────────────────────────────────────────
        print("[Orchestrator] Step 3: Searching...")
        search_results = search_agent.search(plan, max_results=max_results)

        if len(search_results) < 5:
            print("[Orchestrator] Too few results, retrying with simpler query...")
            plan["priority_platforms"] = []
            search_results = search_agent.search(plan, max_results=max_results)

        # ── Step 4: Collect ───────────────────────────────────────────────────
        print("[Orchestrator] Step 4: Collecting listings...")
        listings = collection_agent.collect(
            search_results, max_results=max_results, min_price=min_price
        )

        if len(listings) < 3:
            print("[Orchestrator] Too few listings, retrying with relaxed min_price...")
            listings = collection_agent.collect(
                search_results, max_results=max_results, min_price=10.0
            )

        # ── Step 5: Trust ─────────────────────────────────────────────────────
        print("[Orchestrator] Step 5: Evaluating trust...")
        listings = trust_agent.evaluate(listings)

        trusted = [l for l in listings if l.get("is_trusted")]
        working_listings = trusted if len(trusted) >= 2 else listings

        # ── Step 6: Decision ──────────────────────────────────────────────────
        print("[Orchestrator] Step 6: Deciding best option...")
        ranked = decision_agent.decide(working_listings, product_query=product_name)

        # ── Step 7: Recommend ─────────────────────────────────────────────────
        print("[Orchestrator] Step 7: Generating recommendation...")
        best = rec_agent.recommend(ranked, product_query=product_name)

        # Avoid recommending the same URL user already gave
        if best and user_input.startswith("http"):
            def normalize(u):
                p = urlparse(u)
                return (p.netloc + p.path).rstrip("/")

            if normalize(best.get("link", "")) == normalize(user_input):
                for alt in ranked[1:]:
                    if normalize(alt.get("link", "")) != normalize(user_input):
                        best = alt
                        break

        print("[Orchestrator] Done!")
        return product_name, listings, best