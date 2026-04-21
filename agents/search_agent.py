import traceback
from serpapi import GoogleSearch
from config import SERP_API_KEY


class SearchAgent:
    """
    Uses SerpAPI to run multiple targeted searches:
    - Priority platform search (from planner's plan)
    - General India search
    - Global search
    Deduplicates and returns combined results.
    """

    def search(self, plan: dict, max_results: int = 20) -> list:
        if not SERP_API_KEY:
            print("[SearchAgent] SERP_API_KEY not set.")
            return []

        product_query = plan.get("product_query", "")
        priority_platforms = plan.get("priority_platforms", [])

        if not product_query:
            print("[SearchAgent] No product query in plan.")
            return []

        def run_query(q: str, num: int) -> list:
            try:
                params = {
                    "engine": "google",
                    "q": q,
                    "num": num,
                    "api_key": SERP_API_KEY,
                    "gl": "in",
                    "hl": "en"
                }
                results = GoogleSearch(params).get_dict()
                return results.get("organic_results", [])
            except Exception as e:
                print(f"[SearchAgent] Query failed: {e}")
                traceback.print_exc()
                return []

        all_results = []

        # Query 1: Priority platforms from planner
        if priority_platforms:
            site_filter = " OR ".join([f"site:{s}" for s in priority_platforms])
            q1 = f"{product_query} buy price {site_filter}"
            all_results.extend(run_query(q1, max_results))

        # Query 2: General India search
        q2 = f"{product_query} best price buy online india"
        all_results.extend(run_query(q2, max_results))

        # Query 3: Shopping focused
        q3 = f"{product_query} lowest price india 2024"
        all_results.extend(run_query(q3, max_results // 2))

        # Deduplicate by normalized URL
        seen = set()
        unique = []
        for r in all_results:
            link = r.get("link") or r.get("url", "")
            key = link.split("?")[0].rstrip("/")
            if key and key not in seen:
                seen.add(key)
                unique.append(r)

        print(f"[SearchAgent] Found {len(unique)} unique results.")
        return unique
