from flask import Blueprint, request, jsonify, g
from backend.models.models import db, Customer, AiConversationLog
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.services.ai_service import ask_assistant, AiServiceError

ai_bp = Blueprint("ai", __name__, url_prefix="/api/customer")


@ai_bp.route("/ai-assistant", methods=["POST"])
@token_required(["customer"])       # customer-only: restaurants/admins get 403 automatically
@require_permission("customer.ai_assistant")  # admin can also disable per-customer
def ai_assistant():
    # Customer is resolved ONLY from the authenticated JWT (g.user_id).
    # Any customer_id in the request body, if present, is ignored entirely.
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    if not customer:
        return jsonify({"error": "Customer profile not found."}), 404

    data = request.get_json(force=True, silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []
    if not isinstance(history, list):
        history = []

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400
    if len(message) > 2000:
        return jsonify({"error": "Message is too long."}), 400

    try:
        reply = ask_assistant(customer, message, history)
        db.session.add(AiConversationLog(customer_id=customer.id, message=message, response=reply))
        db.session.commit()
        return jsonify({"reply": reply}), 200
    except AiServiceError as e:
        db.session.rollback()
        try:
            db.session.add(AiConversationLog(customer_id=customer.id, message=message, error=str(e)))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # Graceful fallback -- never crash the app if the AI provider is down/misconfigured.
        return jsonify({"error": str(e), "fallback": True}), 503
    except Exception as e:
        # Catch-all: ANY other unexpected error (a DB relationship issue, a
        # serialization edge case, etc.) must still come back as JSON with a
        # useful message -- never as Flask's default HTML 500 page. An HTML
        # error body makes the frontend's err.response.data.error lookup
        # silently fail and fall back to a generic "Something went wrong."
        db.session.rollback()
        try:
            db.session.add(AiConversationLog(customer_id=customer.id, message=message, error=f"Unexpected: {e}"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        import traceback
        traceback.print_exc()  # goes to the Flask server console/log for debugging
        return jsonify({
            "error": "The AI Assistant hit an unexpected error. Please try again.",
            "fallback": True,
        }), 500