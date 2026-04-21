import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

CAPTCHA_PHRASES = [
    "are you a human", "are you human", "robot", "captcha",
    "verify", "access denied", "just a moment", "checking your browser",
    "please wait", "enable javascript", "ddos protection", "security check"
]


class ProductAgent:

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def _is_captcha(self, text: str) -> bool:
        """Check if extracted text is a CAPTCHA page response."""
        if not text:
            return False
        t = text.lower()
        return any(phrase in t for phrase in CAPTCHA_PHRASES)

    def extract_product(self, link: str) -> str:
        """Extract human-friendly product title from URL."""
        try:
            resp = requests.get(link, headers=self.HEADERS, timeout=12, allow_redirects=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            title = None

            # 1. JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "")
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict) and item.get("name"):
                            title = item["name"]
                            break
                    if title:
                        break
                except Exception:
                    continue

            # 2. Amazon specific
            if not title:
                el = soup.find(id="productTitle")
                if el:
                    title = el.get_text(strip=True)

            # 3. H1
            if not title:
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text(strip=True)

            # 4. OG title
            if not title:
                og = soup.find("meta", property="og:title")
                if og:
                    title = og.get("content", "").strip()

            # 5. Page title
            if not title and soup.title:
                title = soup.title.get_text(strip=True)

            # CAPTCHA check — if title is captcha response, discard it
            if title and self._is_captcha(title):
                print(f"[ProductAgent] CAPTCHA detected, title discarded: {title[:50]}")
                return "Unknown Product"

            if title:
                for noise in ["- Amazon.in", "- Flipkart", "| Flipkart",
                              "- Croma", "| Amazon", "Buy Online"]:
                    title = title.replace(noise, "").strip()
                title = title.split("|")[0].split(" - ")[0].strip()

            return title or "Unknown Product"

        except Exception as e:
            print(f"[ProductAgent] extract_product failed: {e}")
            return "Unknown Product"

    def extract_price_rating(self, link: str, min_price: float = 50.0) -> dict:
        result = {
            "name": None,
            "price": None,
            "rating": None,
            "rating_count": None,
            "shipping": 0,
            "thumbnail": None,
            "link": link
        }

        try:
            resp = requests.get(link, headers=self.HEADERS, timeout=12)
            soup = BeautifulSoup(resp.text, "html.parser")
            domain = urlparse(link).netloc.lower()
            MIN = float(min_price or 50.0)

            # CAPTCHA check on full page
            page_text = soup.get_text()[:500].lower()
            if self._is_captcha(page_text):
                print(f"[ProductAgent] CAPTCHA page detected for {link[:60]}")
                return result

            def parse_price(text: str):
                if not text:
                    return None
                text = text.replace('\xa0', ' ').replace(',', '')
                m = re.search(r'(?:₹|Rs\.?|INR)\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
                if m:
                    try:
                        v = float(m.group(1))
                        return v if MIN <= v <= 1000000 else None
                    except Exception:
                        pass
                return None

            # JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "")
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict):
                            if item.get("name") and not result["name"]:
                                result["name"] = item["name"]

                            offers = item.get("offers")
                            if offers:
                                if isinstance(offers, list):
                                    offers = offers[0]
                                if isinstance(offers, dict):
                                    p = offers.get("price") or offers.get("lowPrice")
                                    if p is not None:
                                        try:
                                            v = float(str(p).replace(',', ''))
                                            if MIN <= v <= 1000000:
                                                result["price"] = v
                                        except Exception:
                                            pass

                            agg = item.get("aggregateRating")
                            if agg and isinstance(agg, dict):
                                rv = agg.get("ratingValue")
                                rc = agg.get("reviewCount") or agg.get("ratingCount")
                                try:
                                    rv_f = float(rv)
                                    if 1.0 <= rv_f <= 5.0:
                                        result["rating"] = rv_f
                                        result["rating_count"] = rc
                                except Exception:
                                    pass
                    if result["price"]:
                        break
                except Exception:
                    continue

            # Meta price
            if result["price"] is None:
                for prop in ["product:price:amount", "og:price:amount"]:
                    meta = soup.find("meta", {"property": prop})
                    if meta:
                        result["price"] = parse_price(meta.get("content", ""))
                        if result["price"]:
                            break

            # Amazon selectors
            if result["price"] is None and "amazon" in domain:
                for sel_id in ["priceblock_ourprice", "priceblock_dealprice", "price_inside_buybox"]:
                    el = soup.find(id=sel_id)
                    if el:
                        result["price"] = parse_price(el.get_text())
                        if result["price"]:
                            break
                if result["price"] is None:
                    whole = soup.find("span", {"class": "a-price-whole"})
                    frac  = soup.find("span", {"class": "a-price-fraction"})
                    if whole:
                        txt = whole.get_text(strip=True).replace(",", "")
                        frac_txt = frac.get_text(strip=True) if frac else "00"
                        try:
                            v = float(f"{txt}.{frac_txt}")
                            if MIN <= v <= 1000000:
                                result["price"] = v
                        except Exception:
                            pass
                if result["rating"] is None:
                    rat = (soup.find("span", {"id": "acrPopover"}) or
                           soup.find("span", {"class": "a-icon-alt"}))
                    if rat:
                        m = re.search(r'([\d\.]+)\s*out of', rat.get_text())
                        if m:
                            try:
                                rv = float(m.group(1))
                                if 1.0 <= rv <= 5.0:
                                    result["rating"] = rv
                            except Exception:
                                pass

            # Flipkart selectors
            if result["price"] is None and "flipkart" in domain:
                for cls in ["_30jeq3 _16Jk6d", "_30jeq3", "Nx9bqj CxhGGd"]:
                    el = soup.find("div", {"class": cls})
                    if el:
                        result["price"] = parse_price(el.get_text())
                        if result["price"]:
                            break
                if result["rating"] is None:
                    rat = soup.find("div", {"class": "_3LWZlK"})
                    if rat:
                        try:
                            rv = float(rat.get_text(strip=True))
                            if 1.0 <= rv <= 5.0:
                                result["rating"] = rv
                        except Exception:
                            pass

            # Thumbnail
            og_img = soup.find("meta", property="og:image")
            if og_img:
                result["thumbnail"] = og_img.get("content")

            return result

        except Exception as e:
            print(f"[ProductAgent] extract_price_rating failed for {link}: {e}")
            return result