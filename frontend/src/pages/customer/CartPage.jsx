import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { updateCartItem, removeCartItem, clearCart } from "../../services/endpoints";
import { useCart } from "../../hooks/CartContext";

export default function CartPage() {
  const { cart, refreshCart } = useCart();
  const navigate = useNavigate();

  useEffect(() => { refreshCart(); }, [refreshCart]);

  async function changeQty(item, delta) {
    const newQty = item.quantity + delta;
    await updateCartItem(item.id, newQty);
    refreshCart();
  }

  async function remove(item) {
    await removeCartItem(item.id);
    refreshCart();
  }

  async function handleClear() {
    await clearCart();
    refreshCart();
  }

  if (cart.items.length === 0) {
    return (
      <div className="container" style={{ paddingTop: 60 }}>
        <div className="empty-state">
          <div style={{ fontSize: 44 }}>🛒</div>
          <h3>Your cart is empty</h3>
          <p>Browse our menu and add something delicious.</p>
          <button className="btn btn-primary" onClick={() => navigate("/")}>Browse Food</button>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 760 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Your Cart</h2>
        <button className="btn btn-ghost btn-sm" onClick={handleClear}>Clear Cart</button>
      </div>

      <div className="card" style={{ padding: 0, overflow: "hidden", marginTop: 10 }}>
        {cart.items.map((item, idx) => (
          <div key={item.id} style={{ display: "flex", alignItems: "center", gap: 14, padding: 16, borderBottom: idx < cart.items.length - 1 ? "1px solid var(--gray-100)" : "none" }}>
            <div style={{ width: 56, height: 56, background: "var(--orange-light)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, flexShrink: 0 }}>
              🍛
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700 }}>{item.food_name}</div>
              <div style={{ fontSize: 13, color: "var(--gray-500)" }}>{item.restaurant} · ₹{item.unit_price} each</div>
              {!item.is_available && <div style={{ fontSize: 12.5, color: "var(--red)" }}>No longer available</div>}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <button className="btn btn-outline btn-sm" onClick={() => changeQty(item, -1)}>−</button>
              <span style={{ minWidth: 20, textAlign: "center", fontWeight: 700 }}>{item.quantity}</span>
              <button className="btn btn-outline btn-sm" onClick={() => changeQty(item, 1)}>+</button>
            </div>
            <div style={{ minWidth: 70, textAlign: "right", fontWeight: 700 }}>₹{item.line_total}</div>
            <button className="btn btn-ghost btn-sm" onClick={() => remove(item)} title="Remove">✕</button>
          </div>
        ))}
      </div>

      <div className="card" style={{ padding: 18, marginTop: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}><span>Subtotal</span><span>₹{cart.subtotal}</span></div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}><span>Delivery Fee</span><span>₹{cart.delivery_fee}</span></div>
        <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700, fontSize: 18, borderTop: "1px solid var(--gray-100)", paddingTop: 10, marginTop: 6 }}>
          <span>Total</span><span style={{ color: "var(--orange)" }}>₹{cart.total}</span>
        </div>
        <button className="btn btn-primary btn-block" style={{ marginTop: 16 }} onClick={() => navigate("/checkout")}>
          Proceed to Checkout
        </button>
      </div>
    </div>
  );
}
