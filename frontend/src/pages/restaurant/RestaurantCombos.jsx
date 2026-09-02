import { useEffect, useState } from "react";
import { getOwnCombos, createCombo, updateCombo, deleteCombo, getOwnFoods } from "../../services/endpoints";

const emptyForm = { name: "", description: "", combo_price: "", image_url: "", start_date: "", end_date: "", is_active: true, items: [] };

export default function RestaurantCombos() {
  const [combos, setCombos] = useState([]);
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([getOwnCombos(), getOwnFoods()])
      .then(([comboRes, foodRes]) => { setCombos(comboRes.data); setFoods(foodRes.data); })
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  function openAdd() {
    setForm(emptyForm);
    setEditingId(null);
    setError("");
    setShowForm(true);
  }

  function openEdit(combo) {
    setForm({
      name: combo.name, description: combo.description || "", combo_price: combo.combo_price,
      image_url: combo.image_url || "",
      start_date: combo.start_date ? combo.start_date.slice(0, 16) : "",
      end_date: combo.end_date ? combo.end_date.slice(0, 16) : "",
      is_active: combo.is_active,
      items: combo.items.map((i) => ({ food_id: i.food_id, quantity: i.quantity })),
    });
    setEditingId(combo.id);
    setError("");
    setShowForm(true);
  }

  function addItemRow() {
    if (foods.length === 0) return;
    setForm((f) => ({ ...f, items: [...f.items, { food_id: foods[0].id, quantity: 1 }] }));
  }

  function updateItemRow(idx, field, value) {
    setForm((f) => ({ ...f, items: f.items.map((it, i) => (i === idx ? { ...it, [field]: value } : it)) }));
  }

  function removeItemRow(idx) {
    setForm((f) => ({ ...f, items: f.items.filter((_, i) => i !== idx) }));
  }

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    if (form.items.length === 0) {
      setError("Add at least one food item to the combo.");
      return;
    }
    setSaving(true);
    const payload = {
      ...form,
      combo_price: parseFloat(form.combo_price),
      items: form.items.map((it) => ({ food_id: parseInt(it.food_id, 10), quantity: parseInt(it.quantity, 10) })),
      start_date: form.start_date || null,
      end_date: form.end_date || null,
    };
    try {
      if (editingId) await updateCombo(editingId, payload);
      else await createCombo(payload);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message || "Failed to save combo.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(combo) {
    if (!confirm(`Delete combo "${combo.name}"?`)) return;
    await deleteCombo(combo.id);
    load();
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Combos & Bundles</h2>
        <button className="btn btn-primary" onClick={openAdd} disabled={foods.length === 0}>+ New Combo</button>
      </div>
      {foods.length === 0 && <div className="alert alert-error">Add some food items first before creating a combo.</div>}

      {showForm && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <h4>{editingId ? "Edit Combo" : "New Combo"}</h4>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleSave}>
            <div className="grid grid-2">
              <div className="field">
                <label>Combo Name</label>
                <input className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="field">
                <label>Combo Price (₹)</label>
                <input className="input" type="number" step="0.01" required value={form.combo_price} onChange={(e) => setForm({ ...form, combo_price: e.target.value })} />
              </div>
            </div>
            <div className="field">
              <label>Description</label>
              <textarea className="input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="grid grid-2">
              <div className="field">
                <label>Start Date (optional)</label>
                <input className="input" type="datetime-local" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
              </div>
              <div className="field">
                <label>End Date (optional)</label>
                <input className="input" type="datetime-local" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
              </div>
            </div>

            <div className="field">
              <label>Included Items</label>
              {form.items.map((it, idx) => (
                <div key={idx} style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
                  <select className="input" value={it.food_id} onChange={(e) => updateItemRow(idx, "food_id", e.target.value)}>
                    {foods.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                  </select>
                  <input className="input" style={{ width: 90 }} type="number" min="1" value={it.quantity}
                    onChange={(e) => updateItemRow(idx, "quantity", e.target.value)} />
                  <button type="button" className="btn btn-ghost btn-sm" style={{ color: "var(--red)" }} onClick={() => removeItemRow(idx)}>Remove</button>
                </div>
              ))}
              <button type="button" className="btn btn-outline btn-sm" onClick={addItemRow}>+ Add Item</button>
            </div>

            <label style={{ display: "flex", alignItems: "center", gap: 8, margin: "14px 0" }}>
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              Active
            </label>

            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : editingId ? "Save Changes" : "Create Combo"}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="skeleton" style={{ height: 200 }} />
      ) : combos.length === 0 ? (
        <div className="empty-state"><h3>No combos yet</h3><p>Bundle popular items together at a discount.</p></div>
      ) : (
        <div className="grid grid-3">
          {combos.map((c) => (
            <div key={c.id} className="card" style={{ padding: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <h4 style={{ margin: 0 }}>{c.name}</h4>
                <span className={`badge ${c.is_currently_active ? "badge-approved" : "badge-rejected"}`}>
                  {c.is_currently_active ? "Live" : "Inactive"}
                </span>
              </div>
              <p style={{ fontSize: 13.5, color: "var(--gray-700)", margin: "8px 0" }}>
                {c.items.map((i) => `${i.food_name} ×${i.quantity}`).join(", ")}
              </p>
              <div style={{ fontWeight: 700 }}>
                ₹{c.combo_price} <span style={{ fontWeight: 400, fontSize: 12.5, color: "var(--gray-500)", textDecoration: "line-through" }}>₹{c.original_price}</span>
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <button className="btn btn-ghost btn-sm" onClick={() => openEdit(c)}>Edit</button>
                <button className="btn btn-ghost btn-sm" style={{ color: "var(--red)" }} onClick={() => handleDelete(c)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
