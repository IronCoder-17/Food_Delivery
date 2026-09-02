from flask import Blueprint, jsonify, g
from backend.models.models import Customer, Wallet, WalletTransaction
from backend.middleware.auth_middleware import token_required
from backend.services.authority_service import require_permission

wallet_bp = Blueprint("wallet", __name__, url_prefix="/api/wallet")


@wallet_bp.route("", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.wallet")
def get_wallet():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    wallet = Wallet.query.filter_by(customer_id=customer.id).first()
    return jsonify({
        "balance": float(wallet.balance),
        "total_credits": float(wallet.total_credits),
        "total_debits": float(wallet.total_debits),
    }), 200


@wallet_bp.route("/transactions", methods=["GET"])
@token_required(["customer"])
@require_permission("customer.wallet")
def get_transactions():
    customer = Customer.query.filter_by(user_id=g.user_id).first()
    wallet = Wallet.query.filter_by(customer_id=customer.id).first()
    txns = WalletTransaction.query.filter_by(wallet_id=wallet.id).order_by(WalletTransaction.created_at.desc()).all()
    return jsonify([{
        "id": t.id, "type": t.type, "amount": float(t.amount), "reason": t.reason,
        "reference_type": t.reference_type, "reference_id": t.reference_id,
        "balance_after": float(t.balance_after), "created_at": t.created_at.isoformat(),
    } for t in txns]), 200
