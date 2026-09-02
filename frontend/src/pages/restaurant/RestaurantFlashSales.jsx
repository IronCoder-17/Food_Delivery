import { useEffect, useState } from "react";
import {
  getOwnFlashSales, createFlashSale, updateFlashSale, deleteFlashSale, getOwnFoods, getOwnCombos,
} from "../../services/endpoints";

const emptyForm = { target_type: "food", target_id: "", discount_percent: "", start_time: "", end_time: "", max_quantity: "" };

export default function RestaurantFlashSales() {
  const [sales, setSales] = useState([]);
  const [foods, setFoods] = useState([]);
  const [combos, setCombos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([getOwnFlashSales(), getOwnFoods(), getOwnCombos()])
      .then(([salesRes, foodRes, comboRes]) => {
        setSales(salesRes.data); setFoods(foodRes.data); setCombos(comboRes.data);
      })
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  function openAdd() {
    const firstFoodId = foods[0]?.id || "";
    setForm({ ...emptyForm, target_id: firstFoodId });
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
      discount_percent: parseFloat(form.discount_percent),
      start_time: startIso,
      end_time: endIso,
      max_quantity: form.max_quantity ? parseInt(form.max_quantity, 10) : null,
      food_id: form.target_type === "food" ? parseInt(form.target_id, 10) : null,
      combo_id: form.target_type === "combo" ? parseInt(form.target_id, 10) : null,
    };

    setSaving(true);
    try {
      await createFlashSale(payload);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message || "Failed to create flash sale.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(sale) {
    await updateFlashSale(sale.id, { is_active: !sale.is_active });
    load();
  }

  async function handleDelete(sale) {
    if (!confirm("Delete this flash sale?")) return;
    await deleteFlashSale(sale.id);
    load();
  }

  const targetOptions = form.target_type === "food" ? foods : combos;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>🔥 Flash Sales</h2>
        <button className="btn btn-primary" onClick={openAdd} disabled={foods.length === 0 && combos.length === 0}>+ New Flash Sale</button>
      </div>

      {showForm && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <h4>New Flash Sale</h4>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleSave}>
            <div className="grid grid-2">
              <div className="field">
                <label>Applies To</label>
                <select className="input" value={form.target_type}
                  onChange={(e) => setForm({ ...form, target_type: e.target.value, target_id: (e.target.value === "food" ? foods[0]?.id : combos[0]?.id) || "" })}>
                  <option value="food">A Food Item</option>
                  <option value="combo">A Combo</option>
                </select>
              </div>
              <div className="field">
                <label>{form.target_type === "food" ? "Food" : "Combo"}</label>
                <select className="input" required value={form.target_id} onChange={(e) => setForm({ ...form, target_id: e.target.value })}>
                  {targetOptions.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-2">
              <div className="field">
                <label>Discount (%)</label>
                <input className="input" type="number" min="1" max="90" required value={form.discount_percent}
                  onChange={(e) => setForm({ ...form, discount_percent: e.target.value })} />
              </div>
              <div className="field">
                <label>Max Quantity (optional)</label>
                <input className="input" type="number" min="1" value={form.max_quantity}
                  onChange={(e) => setForm({ ...form, max_quantity: e.target.value })} placeholder="Unlimited" />
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
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : "Create Flash Sale"}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="skeleton" style={{ height: 200 }} />
      ) : sales.length === 0 ? (
        <div className="empty-state"><h3>No flash sales yet</h3><p>Create a time-boxed deal to drive urgency.</p></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Item</th><th>Discount</th><th>Window</th><th>Sold / Max</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {sales.map((s) => (
                <tr key={s.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{s.food_name || s.combo_name}</td>
                  <td>{s.discount_percent}%</td>
                  <td style={{ fontSize: 12.5 }}>{new Date(s.start_time).toLocaleString()} → {new Date(s.end_time).toLocaleString()}</td>
                  <td>{s.sold_quantity} / {s.max_quantity ?? "∞"}</td>
                  <td>
                    <button className={`badge ${s.is_currently_live ? "badge-approved" : "badge-rejected"}`} style={{ border: "none", cursor: "pointer" }}
                      onClick={() => toggleActive(s)}>
                      {s.is_currently_live ? "Live" : s.is_active ? "Scheduled/Expired" : "Disabled"}
                    </button>
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
