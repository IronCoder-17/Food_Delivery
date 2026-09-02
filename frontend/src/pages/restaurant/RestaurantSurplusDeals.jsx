import { useEffect, useState } from "react";
import {
  getOwnSurplusDeals, createSurplusDeal, updateSurplusDeal, deleteSurplusDeal, getOwnFoods,
} from "../../services/endpoints";

const emptyForm = { food_id: "", discount_price: "", quantity_total: "", order_deadline: "", expiry_time: "" };

export default function RestaurantSurplusDeals() {
  const [deals, setDeals] = useState([]);
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([getOwnSurplusDeals(), getOwnFoods()])
      .then(([dealsRes, foodRes]) => { setDeals(dealsRes.data); setFoods(foodRes.data); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  function openAdd() {
    setForm({ ...emptyForm, food_id: foods[0]?.id || "" });
    setError("");
    setShowForm(true);
  }

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    const deadlineIso = form.order_deadline ? new Date(form.order_deadline).toISOString() : null;
    const expiryIso = form.expiry_time ? new Date(form.expiry_time).toISOString() : null;
    if (!deadlineIso || !expiryIso) {
      setError("Order deadline and expiry time are required.");
      return;
    }
    setSaving(true);
    try {
      await createSurplusDeal({
        food_id: parseInt(form.food_id, 10),
        discount_price: parseFloat(form.discount_price),
        quantity_total: parseInt(form.quantity_total, 10),
        order_deadline: deadlineIso,
        expiry_time: expiryIso,
      });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message || "Failed to create surplus deal.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(deal) {
    await updateSurplusDeal(deal.id, { is_active: !deal.is_active });
    load();
  }

  async function handleDelete(deal) {
    if (!confirm("Delete this surplus deal?")) return;
    await deleteSurplusDeal(deal.id);
    load();
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>♻️ Surplus / Leftover Deals</h2>
        <button className="btn btn-primary" onClick={openAdd} disabled={foods.length === 0}>+ New Surplus Deal</button>
      </div>
      <p style={{ color: "var(--gray-500)", fontSize: 14, marginTop: -8 }}>
        List near-expiry or surplus food at a discount. You remain responsible for food safety --
        the order deadline and expiry time you set here are shown to customers as-is.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      {showForm && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <h4>New Surplus Deal</h4>
          <form onSubmit={handleSave}>
            <div className="grid grid-2">
              <div className="field">
                <label>Food Item</label>
                <select className="input" required value={form.food_id} onChange={(e) => setForm({ ...form, food_id: e.target.value })}>
                  {foods.map((f) => <option key={f.id} value={f.id}>{f.name} (₹{f.final_price})</option>)}
                </select>
              </div>
              <div className="field">
                <label>Discount Price (₹)</label>
                <input className="input" type="number" min="1" step="0.01" required value={form.discount_price}
                  onChange={(e) => setForm({ ...form, discount_price: e.target.value })} />
              </div>
            </div>
            <div className="field">
              <label>Quantity Available</label>
              <input className="input" type="number" min="1" required value={form.quantity_total}
                onChange={(e) => setForm({ ...form, quantity_total: e.target.value })} />
            </div>
            <div className="grid grid-2">
              <div className="field">
                <label>Order Deadline</label>
                <input className="input" type="datetime-local" required value={form.order_deadline}
                  onChange={(e) => setForm({ ...form, order_deadline: e.target.value })} />
              </div>
              <div className="field">
                <label>Expiry Time</label>
                <input className="input" type="datetime-local" required value={form.expiry_time}
                  onChange={(e) => setForm({ ...form, expiry_time: e.target.value })} />
              </div>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : "Create Surplus Deal"}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="skeleton" style={{ height: 200 }} />
      ) : deals.length === 0 ? (
        <div className="empty-state"><h3>No surplus deals yet</h3></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Dish</th><th>Price</th><th>Window</th><th>Sold / Total</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {deals.map((d) => (
                <tr key={d.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{d.food_name}</td>
                  <td>₹{d.discount_price} <span style={{ textDecoration: "line-through", color: "var(--gray-500)", fontSize: 12 }}>₹{d.original_price}</span></td>
                  <td style={{ fontSize: 12.5 }}>Order by {new Date(d.order_deadline).toLocaleString()}<br />Expires {new Date(d.expiry_time).toLocaleString()}</td>
                  <td>{d.quantity_sold} / {d.quantity_total}</td>
                  <td>
                    <button className={`badge ${d.is_currently_available ? "badge-approved" : "badge-rejected"}`} style={{ border: "none", cursor: "pointer" }} onClick={() => toggleActive(d)}>
                      {d.is_currently_available ? "Available" : d.is_active ? "Expired" : "Disabled"}
                    </button>
                  </td>
                  <td><button className="btn btn-ghost btn-sm" style={{ color: "var(--red)" }} onClick={() => handleDelete(d)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
