"""
Packing Photo Proof. Restaurant uploads a photo after packing; ONLY the
order's own customer, the order's own restaurant, and admins can ever view
it. Images are stored on the server filesystem (NOT in any static/public
folder) and are only ever served through this authenticated,
ownership-checked endpoint -- never as a plain static URL.
"""
import os
import uuid

from flask import Blueprint, request, jsonify, g, send_file, current_app

from backend.models.models import db, Order, Customer, Restaurant, OrderPackingProof, OrderTrackingEvent
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission

packing_proof_bp = Blueprint("packing_proof", __name__, url_prefix="/api/orders")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _upload_dir():
    # Deliberately OUTSIDE any static/public folder -- Flask never auto-serves
    # this directory, so the only way to read a file is through the
    # ownership-checked GET endpoint below.
    path = os.path.join(current_app.instance_path, "packing_proofs")
    os.makedirs(path, exist_ok=True)
    return path


def _can_view(order: Order):
    if g.role == "admin":
        return True
    if g.role == "customer":
        customer = Customer.query.filter_by(user_id=g.user_id).first()
        return bool(customer and order.customer_id == customer.id)
    if g.role == "restaurant":
        restaurant = Restaurant.query.filter_by(user_id=g.user_id).first()
        return bool(restaurant and order.restaurant_id == restaurant.id)
    return False


@packing_proof_bp.route("/<int:order_id>/packing-proof", methods=["POST"])
@token_required(["restaurant"])
@require_permission("restaurant.upload_packing_proof")
def upload_packing_proof(order_id):
    restaurant = Restaurant.query.filter_by(user_id=g.user_id).first()
    order = Order.query.filter_by(id=order_id, restaurant_id=restaurant.id).first()
    if not order:
        return jsonify({"error": "Order not found."}), 404

    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "No image file provided."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE_BYTES:
        return jsonify({"error": "Image is too large (max 5 MB)."}), 400
    if size == 0:
        return jsonify({"error": "Uploaded file is empty."}), 400

    filename = f"order_{order.id}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(_upload_dir(), filename)
    file.save(filepath)

    existing = OrderPackingProof.query.filter_by(order_id=order.id).first()
    if existing:
        old_path = os.path.join(_upload_dir(), os.path.basename(existing.image_path))
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass
        existing.image_path = filename
    else:
        db.session.add(OrderPackingProof(order_id=order.id, image_path=filename))
        db.session.add(OrderTrackingEvent(order_id=order.id, status=order.order_status, note="Packing photo uploaded."))

    db.session.commit()
    return jsonify({"message": "Packing proof uploaded.", "has_packing_proof": True}), 201


@packing_proof_bp.route("/<int:order_id>/packing-proof", methods=["GET"])
@token_required(["customer", "restaurant", "admin"])
def get_packing_proof(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found."}), 404
    if not _can_view(order):
        return jsonify({"error": "Forbidden."}), 403

    proof = OrderPackingProof.query.filter_by(order_id=order.id).first()
    if not proof:
        return jsonify({"error": "No packing proof uploaded for this order."}), 404

    filepath = os.path.join(_upload_dir(), os.path.basename(proof.image_path))
    if not os.path.exists(filepath):
        return jsonify({"error": "Packing proof image is missing on the server."}), 404

    return send_file(filepath)
