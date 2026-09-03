import { useEffect, useState } from "react";
import { adminListCustomers, adminGetCustomer, adminSetCustomerStatus } from "../../services/endpoints";

export default function AdminCustomers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState(null);

  function load() {
    setLoading(true);
    adminListCustomers({ search: search || undefined }).then((res) => setCustomers(res.data)).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function toggleActive(c) {
    await adminSetCustomerStatus(c.id, !c.is_active);
    load();
  }

  async function viewDetail(c) {
    const res = await adminGetCustomer(c.id);
    setDetail(res.data);
  }

  return (
    <div>
      <h2>Customer Management</h2>
      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        <input className="input" style={{ maxWidth: 280 }} placeholder="Search by name or mobile..." value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
        <button className="btn btn-outline btn-sm" onClick={load}>Search</button>
      </div>

      {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Name</th><th>Email</th><th>Mobile</th><th>Status</th><th></th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{c.name}</td>
                  <td>{c.email}</td>
                  <td>{c.mobile_number}</td>
                  <td><span className={`badge ${c.is_active ? "badge-approved" : "badge-rejected"}`}>{c.is_active ? "Active" : "Inactive"}</span></td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <button className="btn btn-sm btn-ghost" onClick={() => viewDetail(c)}>View</button>{" "}
                    <button className="btn btn-sm btn-outline" onClick={() => toggleActive(c)}>{c.is_active ? "Deactivate" : "Activate"}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {customers.length === 0 && <div className="empty-state">No customers found.</div>}
        </div>
      )}

      {detail && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }} onClick={() => setDetail(null)}>
          <div className="card" style={{ padding: 24, maxWidth: 480, width: "90%", maxHeight: "80vh", overflow: "auto" }} onClick={(e) => e.stopPropagation()}>
            <h3>{detail.name}</h3>
            <p style={{ color: "var(--gray-500)" }}>{detail.email} · {detail.mobile_number}</p>
            <div className="grid grid-2" style={{ marginBottom: 14 }}>
              <StatMini label="Orders" value={detail.order_count} />
              <StatMini label="Wallet Balance" value={`₹${detail.wallet_balance}`} />
              <StatMini label="GK Games Played" value={detail.game_sessions_played} />
              <StatMini label="Status" value={detail.is_active ? "Active" : "Inactive"} />
            </div>
            <h4>Recent Orders</h4>
            {detail.orders.length === 0 ? <p style={{ color: "var(--gray-500)" }}>No orders yet.</p> : detail.orders.map((o) => (
              <div key={o.id} style={{ fontSize: 14, padding: "6px 0", borderBottom: "1px solid var(--gray-100)" }}>
                #{o.id} · {o.restaurant_name} · ₹{o.total_amount} · {o.order_status}
              </div>
            ))}
            <button className="btn btn-ghost" onClick={() => setDetail(null)} style={{ marginTop: 14 }}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

function StatMini({ label, value }) {
  return <div className="card" style={{ padding: 10 }}><div style={{ fontSize: 12, color: "var(--gray-500)" }}>{label}</div><div style={{ fontWeight: 700 }}>{value}</div></div>;
}
