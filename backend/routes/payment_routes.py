import hmac
import hashlib
from flask import Blueprint, request, jsonify, g, current_app
from backend.models.models import db, Order, Payment, Customer
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission

payment_bp = Blueprint("payment", __name__, url_prefix="/api/payments")


def _get_razorpay_client():
    import razorpay  # imported lazily so the app still boots without the package installed
    return razorpay.Client(auth=(current_app.config["RAZORPAY_KEY_ID"], current_app.config["RAZORPAY_KEY_SECRET"]))


@payment_bp.route("/razorpay/create-order", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.online_payment")
def create_razorpay_order():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id")

    customer = Customer.query.filter_by(user_id=g.user_id).first()
    order = Order.query.get(order_id)
    if not order or order.customer_id != customer.id:
        return jsonify({"error": "Order not found."}), 404
    if order.payment_method != "razorpay":
        return jsonify({"error": "This order was not created for Razorpay payment."}), 400

    amount_paise = int(round(float(order.total_amount) * 100))

    if not current_app.config["RAZORPAY_ENABLED"]:
        # No RAZORPAY_KEY_ID/SECRET configured. Return a clear error rather
        # than faking a successful payment (no fake payment success logic).
        return jsonify({
            "error": "Razorpay is not configured on this server. Set RAZORPAY_KEY_ID and "
                     "RAZORPAY_KEY_SECRET as environment variables to enable live/test payments."
        }), 503

    client = _get_razorpay_client()
    rp_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"order_{order.id}",
        "payment_capture": 1,
    })

    payment = Payment.query.filter_by(order_id=order.id, method="razorpay").first()
    payment.razorpay_order_id = rp_order["id"]
    db.session.commit()

    return jsonify({
        "razorpay_order_id": rp_order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": current_app.config["RAZORPAY_KEY_ID"],  # publishable key only, never the secret
        "order_id": order.id,
    }), 200


@payment_bp.route("/razorpay/verify", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.online_payment")
def verify_razorpay_payment():
    data = request.get_json(force=True) or {}
    order_id = data.get("order_id")
    rp_order_id = data.get("razorpay_order_id")
    rp_payment_id = data.get("razorpay_payment_id")
    rp_signature = data.get("razorpay_signature")

    customer = Customer.query.filter_by(user_id=g.user_id).first()
    order = Order.query.get(order_id)
    if not order or order.customer_id != customer.id:
        return jsonify({"error": "Order not found."}), 404

    payment = Payment.query.filter_by(order_id=order.id, method="razorpay").first()
    if not payment or payment.razorpay_order_id != rp_order_id:
        return jsonify({"error": "Payment record mismatch."}), 400

    # Verify HMAC-SHA256 signature server-side using the secret key.
    # order_id|payment_id signed with the secret must equal the signature.
    generated_signature = hmac.new(
        key=current_app.config["RAZORPAY_KEY_SECRET"].encode(),
        msg=f"{rp_order_id}|{rp_payment_id}".encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(generated_signature, rp_signature or ""):
        payment.status = "failed"
        order.payment_status = "failed"
        db.session.commit()
        return jsonify({"error": "Payment verification failed. Signature mismatch."}), 400

    payment.razorpay_payment_id = rp_payment_id
    payment.razorpay_signature = rp_signature
    payment.status = "success"
    order.payment_status = "paid"
    db.session.commit()

    return jsonify({"message": "Payment verified successfully.", "order_id": order.id}), 200
