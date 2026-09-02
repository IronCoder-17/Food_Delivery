from backend.models.models import db, Wallet, WalletTransaction


def credit_wallet(customer_id: int, amount: float, reason: str, reference_type: str, reference_id: int = None, txn_type="credit"):
    wallet = Wallet.query.filter_by(customer_id=customer_id).first()
    if not wallet:
        raise ValueError("No wallet found for this customer.")
    wallet.balance = float(wallet.balance) + amount
    wallet.total_credits = float(wallet.total_credits) + amount
    txn = WalletTransaction(
        wallet_id=wallet.id, type=txn_type, amount=amount, reason=reason,
        reference_type=reference_type, reference_id=reference_id,
        balance_after=wallet.balance,
    )
    db.session.add(txn)
    db.session.commit()
    return wallet, txn


def debit_wallet(customer_id: int, amount: float, reason: str, reference_type: str, reference_id: int = None):
    """Raises ValueError if balance is insufficient. All checks happen here,
    server-side, so the balance can never be bypassed from the client."""
    wallet = Wallet.query.filter_by(customer_id=customer_id).first()
    if not wallet:
        raise ValueError("No wallet found for this customer.")
    if float(wallet.balance) < amount:
        raise ValueError("Insufficient wallet balance.")

    wallet.balance = float(wallet.balance) - amount
    wallet.total_debits = float(wallet.total_debits) + amount
    txn = WalletTransaction(
        wallet_id=wallet.id, type="debit", amount=amount, reason=reason,
        reference_type=reference_type, reference_id=reference_id,
        balance_after=wallet.balance,
    )
    db.session.add(txn)
    db.session.commit()
    return wallet, txn
