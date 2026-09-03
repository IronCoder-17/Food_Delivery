import { useEffect, useState } from "react";
import { adminListSurplusDeals } from "../../services/endpoints";

export default function AdminSurplusDeals() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    adminListSurplusDeals()
      .then((res) => setDeals(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Surplus Deals Monitoring</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>Read-only view of surplus deals across every restaurant.</p>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="skeleton" style={{ height: 200 }} />
      ) : deals.length === 0 ? (
        <div className="empty-state"><h3>No surplus deals yet</h3></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Restaurant</th><th>Dish</th><th>Price</th><th>Window</th><th>Sold / Total</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {deals.map((d) => (
                <tr key={d.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{d.restaurant_name}</td>
                  <td>{d.food_name}</td>
                  <td>₹{d.discount_price} <span style={{ textDecoration: "line-through", color: "var(--gray-500)", fontSize: 12 }}>₹{d.original_price}</span></td>
                  <td style={{ fontSize: 12.5 }}>Order by {new Date(d.order_deadline).toLocaleString()}<br />Expires {new Date(d.expiry_time).toLocaleString()}</td>
                  <td>{d.quantity_sold} / {d.quantity_total}</td>
                  <td><span className={`badge ${d.is_currently_available ? "badge-approved" : "badge-rejected"}`}>{d.is_currently_available ? "Available" : d.is_active ? "Expired" : "Disabled"}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
