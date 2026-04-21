import time
import re
from urllib.parse import urlparse
from agents.product_agent import ProductAgent


class CollectionAgent:

    def collect(self, search_results: list, max_results: int = 20, min_price: float = 50.0) -> list:
        pa = ProductAgent()
        data = []
        seen_keys = set()

        for r in search_results[:max_results]:
            link = r.get("link") or r.get("url", "")
            if not link:
                continue

            skip_domains = ["youtube.com", "wikipedia.org", "reddit.com",
                          "quora.com", "facebook.com", "instagram.com",
                          "twitter.com", "pinterest.com", "blog.", "/blog/",
                          "medium.com", "linkedin.com"]
            if any(s in link.lower() for s in skip_domains):
                continue

            price = None
            rating = None
            rating_count = None
            thumbnail = r.get("thumbnail") or r.get("favicon")
            name = r.get("title", "Unknown")

            # Strategy 1: SERP rich snippet
            rs = r.get("rich_snippet") or {}
            top = rs.get("top", {}) if isinstance(rs, dict) else {}
            exts = top.get("extensions") if isinstance(top, dict) else None
            if exts:
                for ext in exts:
                    if not isinstance(ext, str):
                        continue
                    m = re.search(r'(?:Rs\.?|INR|₹)\s*([0-9][0-9,]*)', ext, re.IGNORECASE)
                    if m and price is None:
                        try:
                            v = float(m.group(1).replace(',', ''))
                            if v >= min_price:
                                price = v
                        except Exception:
                            pass
                    rm = re.search(r'([\d\.]+)\s*(?:out of 5|stars)', ext, re.IGNORECASE)
                    if rm and rating is None:
                        try:
                            rv = float(rm.group(1))
                            if 1.0 <= rv <= 5.0:
                                rating = rv
                        except Exception:
                            pass

            # Strategy 2: SERP inline price field
            if price is None:
                for field in ["price", "extracted_price"]:
                    val = r.get(field)
                    if val:
                        try:
                            cleaned = str(val).replace(',','').replace('₹','').replace('Rs','').replace('INR','').strip()
                            v = float(cleaned)
                            if min_price <= v <= 1000000:
                                price = v
                                break
                        except Exception:
                            pass

            # Strategy 3: snippet — ONLY currency-marked prices
            if price is None:
                snippet = r.get("snippet", "") or ""
                matches = re.findall(r'(?:Rs\.?|INR|₹)\s*([0-9][0-9,]+)', snippet, re.IGNORECASE)
                for m in matches:
                    try:
                        v = float(str(m).replace(',', ''))
                        if min_price <= v <= 1000000:
                            price = v
                            break
                    except Exception:
                        pass

            # Strategy 4: scrape product page
            if price is None:
                try:
                    info = pa.extract_price_rating(link, min_price=min_price)
                    scraped_price = info.get("price")
                    if scraped_price and min_price <= scraped_price <= 1000000:
                        price = scraped_price
                    if rating is None and info.get("rating"):
                        rv = info["rating"]
                        if 1.0 <= rv <= 5.0:
                            rating = rv
                    rating_count = info.get("rating_count")
                    if not thumbnail:
                        thumbnail = info.get("thumbnail")
                    if info.get("name"):
                        name = info["name"]
                except Exception as e:
                    print(f"[CollectionAgent] Scrape failed: {e}")

            if price is None:
                print(f"[CollectionAgent] No price: {link[:70]}")
                continue

            # Sanity check: suspicious low price for known brands
            name_lower = name.lower()
            known_brands = ["nike", "adidas", "apple", "samsung", "sony", "oneplus",
                          "iphone", "macbook", "dell", "hp", "lenovo", "asus"]
            if price < 200 and any(b in name_lower or b in link.lower() for b in known_brands):
                print(f"[CollectionAgent] Suspicious price ₹{price} skipped")
                continue

            try:
                domain = urlparse(link).netloc.replace("www.", "")
            except Exception:
                domain = ""

            dedup_key = f"{domain}_{int(price)}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            for noise in ["- Amazon.in", "- Flipkart", "| Flipkart",
                         "Buy Online", "- Croma", "| Amazon", "- Myntra"]:
                name = name.replace(noise, "").strip()

            data.append({
                "name": name[:100],
                "price": price,
                "shipping": 0,
                "rating": rating,
                "rating_count": rating_count,
                "link": link,
                "thumbnail": thumbnail,
                "source": domain,
                "trust_score": 0,
                "is_trusted": False,
            })

            time.sleep(0.2)

        print(f"[CollectionAgent] Collected {len(data)} valid listings.")
        return data