"""
Real AI Assistant backend service (customer-side only).

Design:
  - Uses a configurable AI provider via env vars (never hard-coded, never
    exposed to the frontend):
        AI_API_KEY   -- secret key for the provider
        AI_MODEL     -- model name/id to use
        AI_BASE_URL  -- provider's Messages API endpoint (defaults to
                        Anthropic's public API)
  - The model NEVER invents order status, points, or restaurant data. We
    gather the authenticated customer's real data from the database first
    (orders, loyalty, cart, nearby restaurants/foods) and inject it into the
    system prompt as ground truth, then ask the model to answer using only
    that data.
  - If the AI provider is unavailable/misconfigured, we return a clear
    fallback error instead of crashing or fabricating an answer.
"""
import os
import json
import base64
import requests

from backend.models.models import (
    db, Customer, Order, OrderItem, Cart, CartItem, Food, Restaurant, Category,
)
from backend.services import loyalty_service


class AiServiceError(Exception):
    """Raised when the AI provider can't be reached/authenticated. Caller
    should show a graceful fallback message, never crash the request."""


def _provider_config():
    api_key = os.environ.get("AI_API_KEY", "").strip()
    model = os.environ.get("AI_MODEL", "").strip()
    base_url = os.environ.get("AI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions").strip()
    return api_key, model, base_url


def _build_customer_context(customer: Customer) -> dict:
    """
    Gathers the authenticated customer's OWN data only (never another
    customer's). This dict is serialized into the system prompt as the
    single source of truth the model must ground its answers in.
    """
    orders = (
        Order.query.filter_by(customer_id=customer.id)
        .order_by(Order.created_at.desc()).limit(10).all()
    )
    recent_orders = [{
        "id": o.id,
        "restaurant": o.restaurant.restaurant_name if o.restaurant else None,
        "status": o.order_status,
        "payment_status": o.payment_status,
        "total_amount": float(o.total_amount),
        "placed_at": o.created_at.isoformat(),
        "items": [i.food_name for i in o.items],
    } for o in orders]

    total_spending = sum(float(o.total_amount) for o in orders if o.payment_status == "paid")

    loyalty = loyalty_service.get_or_create_loyalty(customer.id)
    loyalty_summary = loyalty_service.serialize_loyalty_summary(loyalty)

    cart = Cart.query.filter_by(customer_id=customer.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all() if cart else []
    cart_summary = [{
        "food_name": ci.food.name, "quantity": ci.quantity,
        "unit_price": ci.food.final_price,
    } for ci in cart_items]

    available_restaurants = (
        Restaurant.query.filter_by(status="approved").limit(15).all()
    )
    restaurant_names = [r.restaurant_name for r in available_restaurants]

    # A small live menu sample so the model can make grounded food
    # suggestions (name/price/veg/category), never invented dishes.
    sample_foods = (
        Food.query.filter_by(is_available=True).order_by(Food.rating.desc()).limit(30).all()
    )
    menu_sample = [{
        "name": f.name, "price": float(f.final_price), "is_veg": bool(f.is_veg),
        "category": f.category.name if f.category else None,
        "restaurant": f.restaurant.restaurant_name if f.restaurant else None,
    } for f in sample_foods]

    return {
        "customer_name": f"{customer.first_name} {customer.last_name}",
        "recent_orders": recent_orders,
        "total_paid_spending_recent_orders": round(total_spending, 2),
        "loyalty": loyalty_summary,
        "cart": cart_summary,
        "available_restaurants": restaurant_names,
        "menu_sample": menu_sample,
    }


SYSTEM_PROMPT_TEMPLATE = """You are the QuickBite AI Assistant, a helpful food-delivery assistant for a \
single authenticated customer on the QuickBite platform.

Rules you must always follow:
1. You may ONLY use the CUSTOMER_DATA JSON provided below as ground truth for anything \
about this customer's orders, loyalty points/rank, cart, or spending. Never invent, guess, \
or estimate any of these values. If the data needed to answer isn't present in CUSTOMER_DATA, \
say you don't have that information rather than making something up.
2. Only recommend restaurants/food items that appear in CUSTOMER_DATA.available_restaurants \
or CUSTOMER_DATA.menu_sample. Never invent restaurant names, dishes, or prices.
3. Never discuss or reveal any other customer's data -- you only ever have this one \
customer's data available to you.
4. Keep answers concise, friendly, and food-delivery focused (ordering, loyalty, cart, \
payments, order status). If asked something unrelated to the platform, politely redirect.
5. For loyalty questions, use CUSTOMER_DATA.loyalty directly (rank, points, next_rank, \
points_needed_for_next_rank, progress_percent, current_level_benefits).
6. For "what should I order" style questions, suggest 2-4 concrete items from \
CUSTOMER_DATA.menu_sample matching the stated preference (vegetarian, budget, etc).

CUSTOMER_DATA:
{customer_data_json}
"""


def _call_ai_provider(system_prompt: str, user_message: str, conversation_history: list) -> str:
    """
    Calls an OpenAI-compatible chat completions endpoint (OpenRouter by
    default, but works with any OpenAI-compatible provider by changing
    AI_BASE_URL/AI_MODEL). Never hard-codes the key -- always read fresh
    from the environment on each call.
    """
    api_key, model, base_url = _provider_config()
    if not api_key or not model:
        raise AiServiceError(
            "AI Assistant is not configured on this server. Set AI_API_KEY and AI_MODEL "
            "in the backend .env file to enable it."
        )

    messages = [{"role": "system", "content": system_prompt}]
    for turn in conversation_history[-6:]:  # bounded context window
        role = "user" if turn.get("role") == "user" else "assistant"
        content = str(turn.get("content", ""))[:2000]
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model,
        "messages": messages,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # OpenRouter uses these two optional headers for their model leaderboard/rate-limit
        # attribution. Harmless no-ops on other OpenAI-compatible providers.
        "HTTP-Referer": os.environ.get("AI_SITE_URL", "http://localhost"),
        "X-Title": "QuickBite AI Assistant",
    }

    try:
        resp = requests.post(base_url, headers=headers, data=json.dumps(payload), timeout=25)
    except requests.RequestException as e:
        raise AiServiceError(f"Could not reach the AI provider: {e}")

    if resp.status_code in (401, 403):
        raise AiServiceError("AI provider rejected the configured API key.")
    if resp.status_code == 429:
        raise AiServiceError("AI provider rate limit reached. Please try again in a moment.")
    if resp.status_code == 404:
        raise AiServiceError(
            "The configured AI_MODEL is no longer available (free model lineups on OpenRouter "
            "rotate often). Set AI_MODEL=openrouter/free in .env to auto-select an available "
            "free model, or pick a current one from https://openrouter.ai/models?max_price=0."
        )
    if resp.status_code >= 500:
        raise AiServiceError("The AI provider is temporarily unavailable. Please try again shortly.")
    if resp.status_code != 200:
        raise AiServiceError(f"AI provider returned an error (status {resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise AiServiceError("The AI provider returned an empty response.")
    message = choices[0].get("message") or {}
    content = message.get("content")
    reply = (content or "").strip()
    if not reply:
        finish_reason = choices[0].get("finish_reason")
        if finish_reason == "length":
            raise AiServiceError(
                "The AI provider cut the response short (hit its token limit). "
                "Try a shorter recipe or a different AI_MODEL."
            )
        raise AiServiceError(
            "The AI provider returned an empty response (this can happen with some "
            "free/reasoning models on OpenRouter). Try setting AI_MODEL to a different "
            "model, e.g. openai/gpt-4o-mini or anthropic/claude-3.5-sonnet."
        )
    return reply


def _call_ai_provider_vision(system_prompt: str, user_text: str, image_b64: str, image_mime: str) -> str:
    """
    Same OpenAI-compatible endpoint as _call_ai_provider, but sends a
    multimodal message (text + image) for vision-capable models. Requires
    AI_MODEL to point at a vision-capable model (most current OpenRouter
    chat models are); if the configured model can't see images, the
    provider will return a normal error we already handle below.
    """
    api_key, model, base_url = _provider_config()
    if not api_key or not model:
        raise AiServiceError(
            "AI Assistant is not configured on this server. Set AI_API_KEY and AI_MODEL "
            "in the backend .env file to enable it."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}},
            ],
        },
    ]

    payload = {"model": model, "messages": messages}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.environ.get("AI_SITE_URL", "http://localhost"),
        "X-Title": "QuickBite Photo Reorder",
    }

    try:
        resp = requests.post(base_url, headers=headers, data=json.dumps(payload), timeout=30)
    except requests.RequestException as e:
        raise AiServiceError(f"Could not reach the AI provider: {e}")

    if resp.status_code in (401, 403):
        raise AiServiceError("AI provider rejected the configured API key.")
    if resp.status_code == 429:
        raise AiServiceError("AI provider rate limit reached. Please try again in a moment.")
    if resp.status_code == 404:
        raise AiServiceError(
            "The configured AI_MODEL is no longer available, or doesn't support image input. "
            "Set AI_MODEL to a current vision-capable model, e.g. openai/gpt-4o-mini or "
            "anthropic/claude-3.5-sonnet, from https://openrouter.ai/models?modality=text%2Bimage-%3Etext."
        )
    if resp.status_code >= 500:
        raise AiServiceError("The AI provider is temporarily unavailable. Please try again shortly.")
    if resp.status_code != 200:
        raise AiServiceError(f"AI provider returned an error (status {resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise AiServiceError("The AI provider returned an empty response.")
    first_choice = choices[0] or {}
    message_obj = first_choice.get("message") or {}
    content = message_obj.get("content")
    # Some providers return multimodal-style content as a list of blocks
    # instead of a plain string -- normalize either shape.
    if isinstance(content, list):
        content = "".join(  
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    reply = (content or "").strip()
    if not reply:
        finish_reason = first_choice.get("finish_reason")
        if finish_reason == "length":
            raise AiServiceError("The AI provider cut the response short (hit its token limit).")
        raise AiServiceError(
            "The AI provider returned an empty response for this image. Try a clearer, "
            "well-lit photo of just the dish, or a different AI_MODEL."
        )
    return reply


DISH_IDENTIFICATION_SYSTEM_PROMPT = """You identify food dishes from photos for a food-delivery app. \
Look at the photo and respond with ONLY a JSON object (no markdown fences, no preamble) in this \
exact shape: {"dish_name": "short common dish name", "ingredients": ["ingredient1", "ingredient2", ...]}. \
List 3-8 main visible or clearly implied ingredients, lowercase, no quantities or units. \
If the photo does not appear to show food at all, respond with exactly: \
{"dish_name": null, "ingredients": []}."""


def identify_dish_from_image(image_bytes: bytes, mime_type: str) -> dict:
    """Uses the same configured AI provider as the AI Assistant / Recipe-to-Order
    to identify a dish name and likely ingredients from a photo. Raises
    AiServiceError if the provider isn't configured, unreachable, or can't
    make sense of the image -- callers should fall back gracefully (e.g. let
    the customer type the dish name instead), never fabricate a result."""
    if not image_bytes:
        raise AiServiceError("No image to analyze.")

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    reply = _call_ai_provider_vision(
        DISH_IDENTIFICATION_SYSTEM_PROMPT,
        "Identify the dish in this photo and list its main ingredients.",
        image_b64, mime_type,
    )
    try:
        cleaned = reply.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError
    except (ValueError, TypeError, json.JSONDecodeError):
        raise AiServiceError("Could not parse the AI provider's response for this image.")

    dish_name = parsed.get("dish_name")
    dish_name = str(dish_name).strip() if dish_name else None
    ingredients_raw = parsed.get("ingredients")
    ingredients = (
        [str(i).strip() for i in ingredients_raw if str(i).strip()][:15]
        if isinstance(ingredients_raw, list) else []
    )

    if not dish_name and not ingredients:
        raise AiServiceError("Couldn't recognize a dish in that photo. Try a clearer photo, or search by name instead.")

    return {"dish_name": dish_name, "ingredients": ingredients}


def ask_assistant(customer: Customer, message: str, conversation_history: list = None) -> str:
    """
    Main entry point used by the /api/customer/ai-assistant route.
    `customer` MUST already be resolved server-side from the authenticated
    session/JWT -- never from a client-supplied id.
    """
    if not message or not message.strip():
        raise AiServiceError("Message cannot be empty.")

    context = _build_customer_context(customer)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(customer_data_json=json.dumps(context, indent=2))
    reply = _call_ai_provider(system_prompt, message.strip(), conversation_history or [])
    return reply


RECIPE_INGREDIENT_SYSTEM_PROMPT = """You extract ingredient names from recipe text. \
Given the recipe text below, respond with ONLY a JSON array of ingredient name strings \
(no quantities, no units, no instructions, no preamble, no markdown fences) -- for example: \
["paneer", "tomato", "onion", "capsicum", "cheese"]. If the text does not appear to contain \
a recipe or ingredient list, respond with an empty JSON array: []."""


def extract_ingredients_from_text(recipe_text: str) -> list:
    """Uses the same configured AI provider as the AI Assistant to extract
    a plain ingredient list from recipe text. Raises AiServiceError (with
    the same graceful messages as ask_assistant) if the provider isn't
    configured or reachable -- callers should fall back to manual
    ingredient entry in that case, never fabricate a list."""
    if not recipe_text or not recipe_text.strip():
        raise AiServiceError("No recipe text to extract ingredients from.")

    reply = _call_ai_provider(RECIPE_INGREDIENT_SYSTEM_PROMPT, recipe_text.strip()[:6000], [])
    try:
        cleaned = reply.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        ingredients = json.loads(cleaned)
        if not isinstance(ingredients, list):
            raise ValueError
        return [str(i).strip() for i in ingredients if str(i).strip()][:40]
    except (ValueError, TypeError, json.JSONDecodeError):
        raise AiServiceError("Could not parse ingredients from the AI provider's response.")