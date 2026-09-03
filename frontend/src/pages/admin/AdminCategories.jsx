import { useEffect, useState } from "react";
import { adminListCategories, adminAddCategory, adminUpdateCategory, adminDeleteCategory } from "../../services/endpoints";

export default function AdminCategories() {
  const [categories, setCategories] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    adminListCategories().then((res) => setCategories(res.data)).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function handleAdd(e) {
    e.preventDefault();
    setError("");
    try {
      await adminAddCategory({ name });
      setName("");
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleActive(c) {
    await adminUpdateCategory(c.id, { is_active: !c.is_active });
    load();
  }

  async function handleDelete(c) {
    if (!confirm(`Delete category "${c.name}"?`)) return;
    try {
      await adminDeleteCategory(c.id);
      load();
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <div>
      <h2>Category Management</h2>
      <form onSubmit={handleAdd} style={{ display: "flex", gap: 10, marginBottom: 18 }}>
        <input className="input" style={{ maxWidth: 280 }} placeholder="New category name" value={name} onChange={(e) => setName(e.target.value)} required />
        <button className="btn btn-primary">Add Category</button>
      </form>
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? <div className="skeleton" style={{ height: 200 }} /> : (
        <div className="grid grid-4">
          {categories.map((c) => (
            <div key={c.id} className="card" style={{ padding: 16 }}>
              <div style={{ fontWeight: 700 }}>{c.name}</div>
              <div style={{ fontSize: 13, color: "var(--gray-500)", margin: "4px 0 10px" }}>{c.food_count} food items</div>
              <span className={`badge ${c.is_active ? "badge-approved" : "badge-rejected"}`}>{c.is_active ? "Active" : "Inactive"}</span>
              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <button className="btn btn-sm btn-outline" onClick={() => toggleActive(c)}>{c.is_active ? "Deactivate" : "Activate"}</button>
                <button className="btn btn-sm btn-ghost" style={{ color: "var(--red)" }} onClick={() => handleDelete(c)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
