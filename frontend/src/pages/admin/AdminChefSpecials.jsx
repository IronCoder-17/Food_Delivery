import { useEffect, useState } from "react";
import { adminListChefSpecials, adminDeleteChefSpecial } from "../../services/endpoints";

export default function AdminChefSpecials() {
  const [specials, setSpecials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  function load() {
    setLoading(true);
    adminListChefSpecials()
      .then((res) => setSpecials(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  async function handleRemove(special) {
    if (!confirm(`Remove Chef's Special "${special.food_name}" from ${special.restaurant_name}? This can't be undone.`)) return;
    setBusyId(special.id);
    try {
      await adminDeleteChefSpecial(special.id);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Chef's Specials Monitoring</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Review all Chef's Specials across every restaurant. Remove anything inappropriate.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="skeleton" style={{ height: 200 }} />
      ) : specials.length === 0 ? (
        <div className="empty-state"><h3>No Chef's Specials yet</h3></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Restaurant</th><th>Dish</th><th>Special Price</th>
                <th>Window</th><th>Sold / Total</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {specials.map((s) => (
                <tr key={s.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{s.restaurant_name}</td>
                  <td>{s.food_name}</td>
                  <td>₹{s.special_price} <span style={{ textDecoration: "line-through", color: "var(--gray-500)", fontSize: 12 }}>₹{s.original_price}</span></td>
                  <td style={{ fontSize: 12.5 }}>{new Date(s.start_time).toLocaleString()} → {new Date(s.end_time).toLocaleString()}</td>
                  <td>{s.quantity_sold} / {s.quantity_total}</td>
                  <td><span className={`badge ${s.is_currently_live ? "badge-approved" : "badge-rejected"}`}>{s.is_currently_live ? "Live" : s.is_active ? "Scheduled/Expired" : "Disabled"}</span></td>
                  <td>
                    <button className="btn btn-ghost btn-sm" style={{ color: "var(--red)" }} disabled={busyId === s.id} onClick={() => handleRemove(s)}>
                      {busyId === s.id ? "..." : "Remove"}
                    </button>
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
