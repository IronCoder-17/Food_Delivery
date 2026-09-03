import { useEffect, useState } from "react";
import {
  getScheduledOrders, createScheduledOrder, cancelScheduledOrder,
  getRestaurantsPublic, getFoods, getAddresses,
} from "../../services/endpoints";

export default function ScheduledOrdersPage() {
  const [scheduled, setScheduled] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [restaurants, setRestaurants] = useState([]);
  const [restaurantsLoading, setRestaurantsLoading] = useState(false);
  const [restaurantsError, setRestaurantsError] = useState("");
  const [addresses, setAddresses] = useState([]);
  const [restaurantId, setRestaurantId] = useState("");
  const [foods, setFoods] = useState([]);
  const [selectedItems, setSelectedItems] = useState({}); // { food_id: quantity }
  const [scheduledFor, setScheduledFor] = useState("");
  const [addressText, setAddressText] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cod");
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    getScheduledOrders()
      .then((res) => setScheduled(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  function openForm() {
    setFormError("");
    setShowForm(true);
    setRestaurantsLoading(true);
    setRestaurantsError("");
    getRestaurantsPublic()
      .then((res) => setRestaurants(res.data))
      .catch((err) => setRestaurantsError(err.message || "Failed to load restaurants."))
      .finally(() => setRestaurantsLoading(false));
    getAddresses().then((res) => {
      setAddresses(res.data);
      const def = res.data.find((a) => a.is_default);
      if (def) setAddressText(def.address);
    }).catch(() => {});
  }

  useEffect(() => {
    if (!restaurantId) { setFoods([]); return; }
    getFoods({ restaurant_id: restaurantId }).then((res) => setFoods(res.data)).catch(() => {});
    setSelectedItems({});
  }, [restaurantId]);

  function toggleItem(food, checked) {
    setSelectedItems((prev) => {
      const next = { ...prev };
      if (checked) next[food.id] = 1;
      else delete next[food.id];
      return next;
    });
  }

  function setQty(foodId, qty) {
    setSelectedItems((prev) => ({ ...prev, [foodId]: Math.max(1, parseInt(qty, 10) || 1) }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    const items = Object.entries(selectedItems).map(([food_id, quantity]) => ({ food_id: parseInt(food_id, 10), quantity }));
    if (!restaurantId) { setFormError("Select a restaurant."); return; }
    if (items.length === 0) { setFormError("Select at least one item."); return; }
    if (!addressText.trim()) { setFormError("Delivery address is required."); return; }
    if (!scheduledFor) { setFormError("Pick a date & time."); return; }

    setSaving(true);
    try {
      await createScheduledOrder({
        restaurant_id: parseInt(restaurantId, 10),
        items,
        address: addressText.trim(),
        payment_method: paymentMethod,
        scheduled_for: new Date(scheduledFor).toISOString(),
      });
      setShowForm(false);
      load();
    } catch (err) {
      setFormError(err.message || "Failed to schedule order.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCancel(so) {
    if (!confirm("Cancel this scheduled order?")) return;
    try {
      await cancelScheduledOrder(so.id);
      load();
    } catch (err) {
      window.alert(err.message || "Failed to cancel.");
    }
  }

  const statusBadge = { scheduled: "badge-pending", completed: "badge-approved", cancelled: "badge-rejected", failed: "badge-rejected" };

  if (loading) return <div className="container" style={{ paddingTop: 24 }}><div className="skeleton" style={{ height: 220 }} /></div>;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 760 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>🕐 Scheduled Orders</h2>
        {!showForm && <button className="btn btn-primary btn-sm" onClick={openForm}>+ Schedule an Order</button>}
      </div>
      <p style={{ color: "var(--gray-500)", marginTop: 4 }}>
        Book an order for a future date and time. Supports Cash on Delivery or Wallet payment.
      </p>
      {error && <div className="alert alert-error">{error}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="card" style={{ padding: 20, marginBottom: 20 }}>
          <h4 style={{ marginTop: 0 }}>New Scheduled Order</h4>
          {formError && <div className="alert alert-error">{formError}</div>}

          <div className="field">
            <label>Restaurant</label>
            {restaurantsError && <div className="alert alert-error">{restaurantsError}</div>}
            <select className="input" value={restaurantId} disabled={restaurantsLoading} onChange={(e) => setRestaurantId(e.target.value)}>
              <option value="">{restaurantsLoading ? "Loading restaurants..." : "Select a restaurant"}</option>
              {restaurants.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            {!restaurantsLoading && !restaurantsError && restaurants.length === 0 && (
              <div className="hint" style={{ color: "var(--red)" }}>
                No approved restaurants are available yet. A restaurant must be approved by an admin (Admin → Restaurants) before it can be selected here.
              </div>
            )}
          </div>

          {restaurantId && (
            <div className="field">
              <label>Items</label>
              <div style={{ maxHeight: 220, overflowY: "auto", border: "1px solid var(--gray-100)", borderRadius: 8, padding: 8 }}>
                {foods.length === 0 && <div style={{ fontSize: 13.5, color: "var(--gray-500)" }}>No items available at this restaurant.</div>}
                {foods.map((f) => (
                  <div key={f.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 0" }}>
                    <input type="checkbox" checked={f.id in selectedItems} onChange={(e) => toggleItem(f, e.target.checked)} disabled={!f.is_available} />
                    <span style={{ flex: 1, fontSize: 14, opacity: f.is_available ? 1 : 0.5 }}>{f.name} — ₹{f.final_price}{!f.is_available ? " (Sold Out)" : ""}</span>
                    {f.id in selectedItems && (
                      <input className="input" style={{ width: 70 }} type="number" min="1" value={selectedItems[f.id]}
                        onChange={(e) => setQty(f.id, e.target.value)} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="field">
            <label>Date & Time</label>
            <input className="input" type="datetime-local" value={scheduledFor} onChange={(e) => setScheduledFor(e.target.value)} />
          </div>

          {addresses.length > 0 && (
            <div className="field">
              <label>Quick-pick a saved address</label>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {addresses.map((a) => (
                  <button type="button" key={a.id} className="btn btn-outline btn-sm" onClick={() => setAddressText(a.address)}>{a.label}</button>
                ))}
              </div>
            </div>
          )}
          <div className="field">
            <label>Delivery Address</label>
            <textarea className="input" rows={2} value={addressText} onChange={(e) => setAddressText(e.target.value)} />
          </div>

          <div className="field">
            <label>Payment Method</label>
            <select className="input" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
              <option value="cod">Cash on Delivery</option>
              <option value="wallet">Wallet</option>
            </select>
            <div className="hint">Online (Razorpay) payment isn't available for scheduled orders since they're placed automatically at the chosen time.</div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-primary" disabled={saving}>{saving ? "Scheduling..." : "Schedule Order"}</button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      )}

      {scheduled.length === 0 ? (
        <div className="empty-state">
          <div style={{ fontSize: 40 }}>🕐</div>
          <h3>No scheduled orders</h3>
          <p>Plan ahead by booking an order for later.</p>
        </div>
      ) : (
        scheduled.map((so) => (
          <div key={so.id} className="card" style={{ padding: 16, marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>{so.restaurant_name}</strong>
                <div style={{ fontSize: 13, color: "var(--gray-500)" }}>{new Date(so.scheduled_for).toLocaleString()}</div>
              </div>
              <span className={`badge ${statusBadge[so.status] || ""}`}>{so.status}</span>
            </div>
            <div style={{ fontSize: 13.5, marginTop: 8 }}>
              {so.items.map((i) => `${i.food_name} ×${i.quantity}`).join(", ")}
            </div>
            {so.failure_reason && <div style={{ fontSize: 13, color: "var(--red)", marginTop: 4 }}>{so.failure_reason}</div>}
            <div style={{ fontSize: 13, color: "var(--gray-500)", marginTop: 4 }}>Delivery to: {so.address}</div>
            {so.can_cancel && (
              <button className="btn btn-outline btn-sm" style={{ marginTop: 10 }} onClick={() => handleCancel(so)}>Cancel</button>
            )}
          </div>
        ))
      )}
    </div>
  );
}