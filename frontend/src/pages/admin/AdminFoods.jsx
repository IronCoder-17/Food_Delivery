import { useEffect, useState } from "react";
import { adminListFoods, adminUpdateFood, adminDeleteFood } from "../../services/endpoints";

export default function AdminFoods() {
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  function load() {
    setLoading(true);
    adminListFoods().then((res) => setFoods(res.data)).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function toggleAvailability(f) {
    await adminUpdateFood(f.id, { is_available: !f.is_available });
    load();
  }

  async function handleDelete(f) {
    if (!confirm(`Delete "${f.name}"?`)) return;
    await adminDeleteFood(f.id);
    load();
  }

  const filtered = foods.filter((f) => f.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <h2>Food Management (All Restaurants)</h2>
      <input className="input" style={{ maxWidth: 300, marginBottom: 16 }} placeholder="Search foods..." value={search} onChange={(e) => setSearch(e.target.value)} />

      {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Name</th><th>Restaurant</th><th>Category</th><th>Price</th><th>Type</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => (
                <tr key={f.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{f.name}</td>
                  <td>{f.restaurant_name}</td>
                  <td>{f.category}</td>
                  <td>₹{f.final_price}</td>
                  <td><span className={`badge ${f.is_veg ? "badge-veg" : "badge-nonveg"}`}>{f.is_veg ? "Veg" : "Non-Veg"}</span></td>
                  <td>
                    <button className={`badge ${f.is_available ? "badge-approved" : "badge-rejected"}`} style={{ border: "none", cursor: "pointer" }} onClick={() => toggleAvailability(f)}>
                      {f.is_available ? "Available" : "Unavailable"}
                    </button>
                  </td>
                  <td><button className="btn btn-sm btn-ghost" style={{ color: "var(--red)" }} onClick={() => handleDelete(f)}>Delete</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && <div className="empty-state">No food items found.</div>}
        </div>
      )}
    </div>
  );
}
