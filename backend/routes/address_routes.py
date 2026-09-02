"""
Multiple Saved Addresses (Home / Work / Hostel / Other).

All endpoints resolve the caller's Customer.id from their authenticated
token (g.user_id) -- never from client-supplied ids -- so a customer can
only ever see/edit/delete their own addresses.
"""
from flask import Blueprint, request, jsonify, g

from backend.models.models import db, Customer, Address
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission
from backend.utils.validators import is_valid_pincode, is_valid_mobile

address_bp = Blueprint("address", __name__, url_prefix="/api/customer/addresses")

VALID_LABELS = {"Home", "Work", "Hostel", "Other"}
VALID_DELIVERY_INSTRUCTIONS = {"silent_drop", "ring_bell", "call_me"}


def _get_own_customer():
    return Customer.query.filter_by(user_id=g.user_id).first()


def _serialize(a: Address):
    return {
        "id": a.id,
        "label": a.label,
        "contact_name": a.contact_name,
        "contact_phone": a.contact_phone,
        "address": a.address,
        "state_id": a.state_id,
        "city_id": a.city_id,
        "pincode": a.pincode,
        "delivery_instruction": a.delivery_instruction,
        "latitude": float(a.latitude) if a.latitude is not None else None,
        "longitude": float(a.longitude) if a.longitude is not None else None,
        "is_default": bool(a.is_default),
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _validate_payload(data, partial=False):
    """Returns an error message string, or None if valid."""
    if not partial or "label" in data:
        label = (data.get("label") or "").strip()
        if label and label not in VALID_LABELS:
            return f"Label must be one of: {', '.join(sorted(VALID_LABELS))}."
    if not partial or "address" in data:
        if not (data.get("address") or "").strip():
            return "Address is required."
    if data.get("pincode") and not is_valid_pincode(str(data["pincode"]).strip()):
        return "Invalid pincode."
    if data.get("contact_phone") and not is_valid_mobile(str(data["contact_phone"]).strip()):
        return "Invalid contact phone number."
    if data.get("delivery_instruction") and data["delivery_instruction"] not in VALID_DELIVERY_INSTRUCTIONS:
        return f"delivery_instruction must be one of: {', '.join(sorted(VALID_DELIVERY_INSTRUCTIONS))}."
    lat, lng = data.get("latitude"), data.get("longitude")
    if (lat is None) != (lng is None):
        return "Both latitude and longitude must be provided together."
    return None


@address_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.manage_addresses")
def list_addresses():
    customer = _get_own_customer()
    addresses = Address.query.filter_by(customer_id=customer.id) \
        .order_by(Address.is_default.desc(), Address.created_at.desc()).all()
    return jsonify([_serialize(a) for a in addresses]), 200


@address_bp.route("", methods=["POST"])
@token_required(["customer"])
@require_permission("customer.manage_addresses")
def create_address():
    customer = _get_own_customer()
    data = request.get_json(force=True) or {}

    err = _validate_payload(data)
    if err:
        return jsonify({"error": err}), 400

    make_default = bool(data.get("is_default"))
    # First address for a customer is always the default, regardless of what was sent.
    if Address.query.filter_by(customer_id=customer.id).count() == 0:
        make_default = True

    if make_default:
        Address.query.filter_by(customer_id=customer.id, is_default=True).update({"is_default": False})

    addr = Address(
        customer_id=customer.id,
        label=(data.get("label") or "Home").strip(),
        contact_name=(data.get("contact_name") or "").strip() or None,
        contact_phone=(data.get("contact_phone") or "").strip() or None,
        address=data["address"].strip(),
        state_id=data.get("state_id") or None,
        city_id=data.get("city_id") or None,
        pincode=(data.get("pincode") or "").strip() or None,
        delivery_instruction=(data.get("delivery_instruction") or "ring_bell").strip(),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        is_default=make_default,
    )
    db.session.add(addr)
    db.session.commit()
    return jsonify(_serialize(addr)), 201


@address_bp.route("/<int:address_id>", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.manage_addresses")
def update_address(address_id):
    customer = _get_own_customer()
    addr = Address.query.filter_by(id=address_id, customer_id=customer.id).first()
    if not addr:
        return jsonify({"error": "Address not found."}), 404

    data = request.get_json(force=True) or {}
    err = _validate_payload(data, partial=True)
    if err:
        return jsonify({"error": err}), 400

    if "label" in data and (data.get("label") or "").strip():
        addr.label = data["label"].strip()
    if "contact_name" in data:
        addr.contact_name = (data.get("contact_name") or "").strip() or None
    if "contact_phone" in data:
        addr.contact_phone = (data.get("contact_phone") or "").strip() or None
    if "address" in data and (data.get("address") or "").strip():
        addr.address = data["address"].strip()
    if "state_id" in data:
        addr.state_id = data.get("state_id") or None
    if "city_id" in data:
        addr.city_id = data.get("city_id") or None
    if "pincode" in data:
        addr.pincode = (data.get("pincode") or "").strip() or None
    if "delivery_instruction" in data and (data.get("delivery_instruction") or "").strip():
        addr.delivery_instruction = data["delivery_instruction"].strip()
    if "latitude" in data:
        addr.latitude = data.get("latitude")
    if "longitude" in data:
        addr.longitude = data.get("longitude")

    if data.get("is_default"):
        Address.query.filter(Address.customer_id == customer.id, Address.id != addr.id) \
            .update({"is_default": False})
        addr.is_default = True

    db.session.commit()
    return jsonify(_serialize(addr)), 200


@address_bp.route("/<int:address_id>", methods=["DELETE"])
@token_required(["customer"])
@require_permission("customer.manage_addresses")
def delete_address(address_id):
    customer = _get_own_customer()
    addr = Address.query.filter_by(id=address_id, customer_id=customer.id).first()
    if not addr:
        return jsonify({"error": "Address not found."}), 404

    was_default = addr.is_default
    db.session.delete(addr)
    db.session.flush()

    # If we just deleted the default address, promote the most recently
    # created remaining address to default so checkout always has one
    # available (never silently leaves the customer with zero default).
    if was_default:
        next_addr = Address.query.filter_by(customer_id=customer.id) \
            .order_by(Address.created_at.desc()).first()
        if next_addr:
            next_addr.is_default = True

    db.session.commit()
    return jsonify({"message": "Address deleted."}), 200


@address_bp.route("/<int:address_id>/default", methods=["PUT"])
@token_required(["customer"])
@require_permission("customer.manage_addresses")
def set_default_address(address_id):
    customer = _get_own_customer()
    addr = Address.query.filter_by(id=address_id, customer_id=customer.id).first()
    if not addr:
        return jsonify({"error": "Address not found."}), 404

    Address.query.filter(Address.customer_id == customer.id, Address.id != addr.id) \
        .update({"is_default": False})
    addr.is_default = True
    db.session.commit()
    return jsonify(_serialize(addr)), 200
