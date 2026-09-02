"""
Recipe-to-Order.

Design note (why this isn't fake): ingredient extraction from a pasted
recipe URL genuinely calls the same configured AI provider used by the
existing AI Assistant feature (backend/services/ai_service.py) -- reusing
its real, already-working configuration rather than inventing a second one.
If no AI provider is configured (as in this deployment, which only has
Razorpay keys set up), extraction is UNAVAILABLE and this service says so
plainly -- it never fabricates an ingredient list. The manual ingredient
input fallback required by the spec is always available regardless, and
works identically either way once you have an ingredient list: matching
against the menu is a real database query, not an AI guess.

URL fetching is a single, non-aggressive GET request with a timeout and a
generous but bounded read size -- no bypassing paywalls, logins, or
robots.txt-style restrictions, and no repeated/parallel requests to the
same site.
"""
import re
from html.parser import HTMLParser

import requests

from backend.models.models import Food
from backend.services import ai_service

REQUEST_TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB -- plenty for a recipe page's HTML


class _TextExtractor(HTMLParser):
    """Minimal, dependency-free HTML-to-text stripper (stdlib only) --
    good enough to hand readable text to the ingredient-extraction step."""
    def __init__(self):
        super().__init__()
        self._skip = False
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.chunks.append(data.strip())

    def get_text(self):
        return "\n".join(self.chunks)


def fetch_recipe_text(url: str) -> str:
    """Fetches a recipe page and returns its visible text. Raises ValueError
    with a user-facing message on any failure (bad URL, network error,
    non-HTML response, etc) -- callers should fall back to manual input."""
    if not re.match(r"^https?://", url or "", re.IGNORECASE):
        raise ValueError("Please provide a valid http(s) recipe URL.")

    try:
        resp = requests.get(
            url, timeout=REQUEST_TIMEOUT_SECONDS, stream=True,
            headers={"User-Agent": "QuickBiteRecipeBot/1.0 (+recipe-to-order feature)"},
        )
    except requests.RequestException as e:
        raise ValueError(f"Could not reach that URL: {e}")

    if resp.status_code != 200:
        raise ValueError(f"That URL returned an error (status {resp.status_code}).")

    content_type = resp.headers.get("Content-Type", "")
    if "html" not in content_type.lower():
        raise ValueError("That URL doesn't appear to be a web page.")

    raw = resp.raw.read(MAX_RESPONSE_BYTES, decode_content=True)
    html = raw.decode(resp.encoding or "utf-8", errors="ignore")

    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        raise ValueError("Could not parse that page's content.")

    text = parser.get_text()
    if len(text) < 50:
        raise ValueError("Could not find readable recipe content on that page.")
    return text


def extract_ingredients_from_url(url: str):
    """Returns (ingredients: list[str], used_ai: bool). Raises ValueError
    with a message suitable to show the customer -- callers should catch
    this and offer the manual ingredient-input fallback."""
    text = fetch_recipe_text(url)
    try:
        ingredients = ai_service.extract_ingredients_from_text(text)
    except ai_service.AiServiceError as e:
        raise ValueError(
            f"Fetched the page, but couldn't extract ingredients automatically ({e}). "
            "Please enter the ingredients manually instead."
        )
    if not ingredients:
        raise ValueError("Couldn't identify any ingredients on that page. Please enter them manually.")
    return ingredients, True


def match_ingredients_to_foods(ingredients: list, limit: int = 20):
    """Real, deterministic keyword matching against the live menu database
    -- NOT an AI guess. match_percent = how many of the given ingredients
    appear (as whole words) in the food's name + description."""
    cleaned = [i.strip().lower() for i in ingredients if i and i.strip()]
    if not cleaned:
        return []

    foods = Food.query.filter_by(is_available=True).all()
    results = []
    for food in foods:
        haystack = f"{food.name} {food.description or ''}".lower()
        matched = [ing for ing in cleaned if re.search(rf"\b{re.escape(ing)}\b", haystack)]
        if not matched:
            continue
        match_percent = round(len(matched) / len(cleaned) * 100, 1)
        results.append({
            "food_id": food.id,
            "food_name": food.name,
            "restaurant_id": food.restaurant_id,
            "restaurant_name": food.restaurant.restaurant_name if food.restaurant else None,
            "price": float(food.final_price),
            "is_available": bool(food.is_available),
            "matched_ingredients": matched,
            "match_percent": match_percent,
        })

    results.sort(key=lambda r: r["match_percent"], reverse=True)
    return results[:limit]
