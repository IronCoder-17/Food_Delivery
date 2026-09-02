import { useEffect, useState } from "react";
import {
  getOwnChefSpecials, createChefSpecial, updateChefSpecial, deleteChefSpecial, getOwnFoods,
} from "../../services/endpoints";

const emptyForm = { food_id: "", special_price: "", quantity_total: "", start_time: "", end_time: "", description: "", image_url: "" };

function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

function getLiveStatus(special, nowMs) {
  if (!special.is_active) return { label: "Disabled", cls: "badge-rejected" };
  const start = new Date(special.start_time).getTime();
  const end = new Date(special.end_time).getTime();
  if (nowMs < start) return { label: "Scheduled", cls: "badge-pending" };
  if (nowMs > end) return { label: "Expired", cls: "badge-rejected" };
  if (special.quantity_sold >= special.quantity_total) return { label: "Sold Out", cls: "badge-rejected" };
  return { label: "Live", cls: "badge-approved" };
}

export default function RestaurantChefSpecials() {
  const [specials, setSpecials] = useState([]);
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const now = useNow();

  function load() {
    setLoading(true);
    Promise.all([getOwnChefSpecials(), getOwnFoods()])
      .then(([specialsRes, foodRes]) => { setSpecials(specialsRes.data); setFoods(foodRes.data); })
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

    const startIso = form.start_time ? new Date(form.start_time).toISOString() : null;
    const endIso = form.end_time ? new Date(form.end_time).toISOString() : null;
    if (!startIso || !endIso) {
      setError("Start and end time are required.");
      return;
    }

    const payload = {
      food_id: parseInt(form.food_id, 10),
      special_price: parseFloat(form.special_price),
      quantity_total: parseInt(form.quantity_total, 10),
      start_time: startIso,
      end_time: endIso,
      description: form.description || undefined,
      image_url: form.image_url || undefined,
    };

    setSaving(true);
    try {
      await createChefSpecial(payload);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message || "Failed to create Chef's Special.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(special) {
    await updateChefSpecial(special.id, { is_active: !special.is_active });
    load();
  }

  async function handleDelete(special) {
    if (!confirm("Delete this Chef's Special?")) return;
    await deleteChefSpecial(special.id);
    load();
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>👨‍🍳 Chef's Specials</h2>
        <button className="btn btn-primary" onClick={openAdd} disabled={foods.length === 0}>+ New Chef's Special</button>
      </div>
      <p style={{ color: "var(--gray-500)", fontSize: 14, marginTop: -8 }}>
        A limited-time, limited-quantity dish at your own special price -- first come, first served.
        The special price is enforced automatically at checkout.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      {showForm && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <h4>New Chef's Special</h4>
          <form onSubmit={handleSave}>
            <div className="grid grid-2">
              <div className="field">
                <label>Food Item</label>
                <select className="input" required value={form.food_id} onChange={(e) => setForm({ ...form, food_id: e.target.value })}>
                  {foods.map((f) => <option key={f.id} value={f.id}>{f.name} (₹{f.final_price})</option>)}
                </select>
              </div>
              <div className="field">
                <label>Special Price (₹)</label>
                <input className="input" type="number" min="1" step="0.01" required value={form.special_price}
                  onChange={(e) => setForm({ ...form, special_price: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-2">
              <div className="field">
                <label>Quantity Available</label>
                <input className="input" type="number" min="1" required value={form.quantity_total}
                  onChange={(e) => setForm({ ...form, quantity_total: e.target.value })} />
              </div>
              <div className="field">
                <label>Image URL (optional)</label>
                <input className="input" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." />
              </div>
            </div>
            <div className="grid grid-2">
              <div className="field">
                <label>Start Time</label>
                <input className="input" type="datetime-local" required value={form.start_time}
                  onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
              </div>
              <div className="field">
                <label>End Time</label>
                <input className="input" type="datetime-local" required value={form.end_time}
                  onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
              </div>
            </div>
            <div className="field">
              <label>Description (optional)</label>
              <textarea className="input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : "Create Chef's Special"}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="skeleton" style={{ height: 200 }} />
      ) : specials.length === 0 ? (
        <div className="empty-state"><h3>No Chef's Specials yet</h3><p>Create a limited-time dish to drive excitement.</p></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Dish</th><th>Special Price</th><th>Window</th><th>Sold / Total</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {specials.map((s) => (
                <tr key={s.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{s.food_name}</td>
                  <td>₹{s.special_price} <span style={{ textDecoration: "line-through", color: "var(--gray-500)", fontSize: 12 }}>₹{s.original_price}</span></td>
                  <td style={{ fontSize: 12.5 }}>{new Date(s.start_time).toLocaleString()} → {new Date(s.end_time).toLocaleString()}</td>
                  <td>{s.quantity_sold} / {s.quantity_total}</td>
                  <td>
                    {(() => {
                      const status = getLiveStatus(s, now);
                      return (
                        <button className={`badge ${status.cls}`} style={{ border: "none", cursor: "pointer" }}
                          onClick={() => toggleActive(s)}>
                          {status.label}
                        </button>
                      );
                    })()}
                  </td>
                  <td><button className="btn btn-ghost btn-sm" style={{ color: "var(--red)" }} onClick={() => handleDelete(s)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}