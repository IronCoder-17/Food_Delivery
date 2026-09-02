import { useEffect, useState } from "react";
import { getOwnFoods, addFood, updateFood, deleteFood, getCategories, updateFoodInventory, getMoods, getAllergens } from "../../services/endpoints";

const emptyForm = { name: "", category_id: "", is_veg: true, description: "", price: "", discount_percent: 0, preparation_time_minutes: 20, image_url: "", mood_ids: [], allergen_ids: [] };

export default function RestaurantFoods() {
  const [foods, setFoods] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [moods, setMoods] = useState([]);
  const [allergens, setAllergens] = useState([]);

  const [inventoryEditId, setInventoryEditId] = useState(null);
  const [inventoryForm, setInventoryForm] = useState({ track_inventory: false, stock_quantity: "", low_stock_threshold: 5 });
  const [inventoryError, setInventoryError] = useState("");
  const [inventorySaving, setInventorySaving] = useState(false);

  function load() {
    setLoading(true);
    getOwnFoods().then((res) => setFoods(res.data)).finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    getCategories().then((res) => setCategories(res.data));
    getMoods().then((res) => setMoods(res.data)).catch(() => {});
    getAllergens().then((res) => setAllergens(res.data.allergens)).catch(() => {});
  }, []);

  function openAdd() {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(true);
    setError("");
  }

  function openEdit(food) {
    setForm({
      name: food.name, category_id: food.category_id, is_veg: food.is_veg,
      description: food.description || "", price: food.price, discount_percent: food.discount_percent,
      preparation_time_minutes: food.preparation_time_minutes, image_url: food.image_url || "",
      mood_ids: (food.moods || []).map((m) => m.id),
      allergen_ids: (food.allergens || []).map((a) => a.id),
    });
    setEditingId(food.id);
    setShowForm(true);
    setError("");
  }

  function toggleTag(field, id) {
    setForm((f) => {
      const current = f[field] || [];
      return { ...f, [field]: current.includes(id) ? current.filter((x) => x !== id) : [...current, id] };
    });
  }

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    try {
      if (editingId) {
        await updateFood(editingId, form);
      } else {
        await addFood(form);
      }
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleAvailability(food) {
    await updateFood(food.id, { is_available: !food.is_available });
    load();
  }

  async function handleDelete(food) {
    if (!confirm(`Delete "${food.name}"?`)) return;
    await deleteFood(food.id);
    load();
  }

  function openInventory(food) {
    setInventoryError("");
    setInventoryForm({
      track_inventory: food.track_inventory,
      stock_quantity: food.stock_quantity ?? "",
      low_stock_threshold: food.low_stock_threshold ?? 5,
    });
    setInventoryEditId(food.id);
  }

  async function saveInventory(e) {
    e.preventDefault();
    setInventoryError("");
    setInventorySaving(true);
    try {
      await updateFoodInventory(inventoryEditId, {
        track_inventory: inventoryForm.track_inventory,
        stock_quantity: inventoryForm.track_inventory
          ? (inventoryForm.stock_quantity === "" ? 0 : parseInt(inventoryForm.stock_quantity, 10))
          : null,
        low_stock_threshold: parseInt(inventoryForm.low_stock_threshold, 10) || 0,
      });
      setInventoryEditId(null);
      load();
    } catch (err) {
      setInventoryError(err.message || "Failed to update inventory.");
    } finally {
      setInventorySaving(false);
    }
  }

  const filtered = foods.filter((f) => f.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Food Management</h2>
        <button className="btn btn-primary" onClick={openAdd}>+ Add Food</button>
      </div>

      <input className="input" style={{ maxWidth: 300, marginBottom: 16 }} placeholder="Search your foods..." value={search} onChange={(e) => setSearch(e.target.value)} />

      {showForm && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <h4>{editingId ? "Edit Food" : "Add New Food"}</h4>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleSave}>
            <div className="grid grid-2">
              <div className="field">
                <label>Food Name</label>
                <input className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="field">
                <label>Category</label>
                <select className="input" required value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                  <option value="">Select category</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-2">
              <div className="field">
                <label>Price (₹)</label>
                <input className="input" type="number" step="0.01" required value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
              </div>
              <div className="field">
                <label>Discount (%)</label>
                <input className="input" type="number" step="0.01" value={form.discount_percent} onChange={(e) => setForm({ ...form, discount_percent: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-2">
              <div className="field">
                <label>Veg / Non-Veg</label>
                <select className="input" value={form.is_veg} onChange={(e) => setForm({ ...form, is_veg: e.target.value === "true" })}>
                  <option value="true">Vegetarian</option>
                  <option value="false">Non-Vegetarian</option>
                </select>
              </div>
              <div className="field">
                <label>Preparation Time (min)</label>
                <input className="input" type="number" value={form.preparation_time_minutes} onChange={(e) => setForm({ ...form, preparation_time_minutes: e.target.value })} />
              </div>
            </div>
            <div className="field">
              <label>Description</label>
              <textarea className="input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="field">
              <label>Image URL (optional)</label>
              <input className="input" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." />
            </div>
            {moods.length > 0 && (
              <div className="field">
                <label>Mood Tags (helps customers find this dish by craving)</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {moods.map((m) => (
                    <label key={m.id} style={{
                      display: "flex", alignItems: "center", gap: 5, fontSize: 13.5,
                      border: "1px solid var(--gray-300)", borderRadius: 8, padding: "5px 10px", cursor: "pointer",
                      background: (form.mood_ids || []).includes(m.id) ? "var(--orange-light, #ffe8d6)" : "transparent",
                    }}>
                      <input type="checkbox" checked={(form.mood_ids || []).includes(m.id)} onChange={() => toggleTag("mood_ids", m.id)} />
                      {m.emoji} {m.name}
                    </label>
                  ))}
                </div>
              </div>
            )}
            {allergens.length > 0 && (
              <div className="field">
                <label>Ingredient & Allergen Tags</label>
                <p style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: -4, marginBottom: 8 }}>
                  This information is shown to customers as provided by you. Please keep it accurate.
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {allergens.map((a) => (
                    <label key={a.id} style={{
                      display: "flex", alignItems: "center", gap: 5, fontSize: 13.5,
                      border: "1px solid var(--gray-300)", borderRadius: 8, padding: "5px 10px", cursor: "pointer",
                      background: (form.allergen_ids || []).includes(a.id) ? "#eef1f5" : "transparent",
                    }}>
                      <input type="checkbox" checked={(form.allergen_ids || []).includes(a.id)} onChange={() => toggleTag("allergen_ids", a.id)} />
                      {a.name}
                    </label>
                  ))}
                </div>
              </div>
            )}
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary">{editingId ? "Save Changes" : "Add Food"}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {inventoryEditId !== null && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <h4>Manage Inventory</h4>
          {inventoryError && <div className="alert alert-error">{inventoryError}</div>}
          <form onSubmit={saveInventory}>
            <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <input
                type="checkbox" checked={inventoryForm.track_inventory}
                onChange={(e) => setInventoryForm((f) => ({ ...f, track_inventory: e.target.checked }))}
              />
              Track stock for this item (auto sold-out at 0)
            </label>
            {inventoryForm.track_inventory && (
              <div className="grid grid-2">
                <div className="field">
                  <label>Stock Quantity</label>
                  <input className="input" type="number" min="0" value={inventoryForm.stock_quantity}
                    onChange={(e) => setInventoryForm((f) => ({ ...f, stock_quantity: e.target.value }))} />
                </div>
                <div className="field">
                  <label>Low Stock Threshold</label>
                  <input className="input" type="number" min="0" value={inventoryForm.low_stock_threshold}
                    onChange={(e) => setInventoryForm((f) => ({ ...f, low_stock_threshold: e.target.value }))} />
                </div>
              </div>
            )}
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary" disabled={inventorySaving}>{inventorySaving ? "Saving..." : "Save Inventory"}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setInventoryEditId(null)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="skeleton" style={{ height: 300 }} />
      ) : filtered.length === 0 ? (
        <div className="empty-state"><h3>No food items yet</h3><p>Add your first dish to get started.</p></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Name</th><th>Category</th><th>Price</th><th>Discount</th><th>Available</th><th>Stock</th><th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => (
                <tr key={f.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>
                    <span className={`badge ${f.is_veg ? "badge-veg" : "badge-nonveg"}`} style={{ marginRight: 8 }}>{f.is_veg ? "V" : "NV"}</span>
                    {f.name}
                  </td>
                  <td>{f.category}</td>
                  <td>₹{f.final_price} {f.discount_percent > 0 && <span style={{ color: "var(--gray-500)", textDecoration: "line-through", fontSize: 12.5 }}>₹{f.price}</span>}</td>
                  <td>{f.discount_percent}%</td>
                  <td>
                    <button className={`badge ${f.is_available ? "badge-approved" : "badge-rejected"}`} style={{ border: "none", cursor: "pointer" }} onClick={() => toggleAvailability(f)}>
                      {f.is_available ? "Available" : "Unavailable"}
                    </button>
                  </td>
                  <td>
                    {f.track_inventory ? (
                      <span style={{ fontSize: 13, color: f.is_low_stock ? "var(--orange)" : "var(--gray-700)" }}>
                        {f.stock_quantity} in stock{f.is_low_stock ? " ⚠️" : ""}
                      </span>
                    ) : (
                      <span style={{ fontSize: 13, color: "var(--gray-500)" }}>Not tracked</span>
                    )}
                  </td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => openInventory(f)}>Inventory</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => openEdit(f)}>Edit</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(f)} style={{ color: "var(--red)" }}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
