import { useEffect, useState } from "react";
import { adminListRestaurants, adminApproveRestaurant, adminRejectRestaurant, adminSetRestaurantStatus, adminDeleteRestaurant } from "../../services/endpoints";

export default function AdminRestaurants() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");

  function load() {
    setLoading(true);
    adminListRestaurants({ status: statusFilter || undefined, search: search || undefined })
      .then((res) => setRestaurants(res.data))
      .finally(() => setLoading(false));
  }
  useEffect(load, [statusFilter]);

  async function handleApprove(r) { await adminApproveRestaurant(r.id); load(); }
  async function handleReject(r) { await adminRejectRestaurant(r.id); load(); }
  async function handleDeactivate(r) { await adminSetRestaurantStatus(r.id, "deactivated"); load(); }
  async function handleReactivate(r) { await adminSetRestaurantStatus(r.id, "approved"); load(); }
  async function handleDelete(r) {
    if (!confirm(`Permanently delete "${r.restaurant_name}"? This cannot be undone.`)) return;
    await adminDeleteRestaurant(r.id);
    load();
  }

  return (
    <div>
      <h2>Restaurant Management</h2>
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
        <input className="input" style={{ maxWidth: 260 }} placeholder="Search restaurants..." value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
        <button className="btn btn-outline btn-sm" onClick={load}>Search</button>
        {["", "pending", "approved", "rejected", "deactivated"].map((s) => (
          <button key={s} className="btn btn-sm" onClick={() => setStatusFilter(s)}
            style={{ background: statusFilter === s ? "var(--orange)" : "var(--white)", color: statusFilter === s ? "#fff" : "var(--ink)", border: "1px solid var(--gray-300)" }}>
            {s === "" ? "All" : s}
          </button>
        ))}
      </div>

      {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Restaurant</th><th>Owner</th><th>Email</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {restaurants.map((r) => (
                <tr key={r.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{r.restaurant_name}</td>
                  <td>{r.owner_name}</td>
                  <td>{r.email}</td>
                  <td><span className={`badge badge-${r.status === "approved" ? "approved" : r.status === "pending" ? "pending" : "rejected"}`}>{r.status}</span></td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    {r.status === "pending" && (
                      <>
                        <button className="btn btn-sm btn-primary" onClick={() => handleApprove(r)}>Approve</button>{" "}
                        <button className="btn btn-sm btn-outline" onClick={() => handleReject(r)}>Reject</button>
                      </>
                    )}
                    {r.status === "approved" && (
                      <button className="btn btn-sm btn-outline" onClick={() => handleDeactivate(r)}>Deactivate</button>
                    )}
                    {(r.status === "deactivated" || r.status === "rejected") && (
                      <button className="btn btn-sm btn-outline" onClick={() => handleReactivate(r)}>Reactivate</button>
                    )}{" "}
                    <button className="btn btn-sm btn-ghost" style={{ color: "var(--red)" }} onClick={() => handleDelete(r)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {restaurants.length === 0 && <div className="empty-state">No restaurants found.</div>}
        </div>
      )}
    </div>
  );
}
