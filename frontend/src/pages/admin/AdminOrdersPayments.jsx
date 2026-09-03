import { useEffect, useState } from "react";
import { adminListOrders, adminListPayments } from "../../services/endpoints";

export function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [orderStatus, setOrderStatus] = useState("");

  function load() {
    setLoading(true);
    adminListOrders({ order_status: orderStatus || undefined }).then((res) => setOrders(res.data)).finally(() => setLoading(false));
  }
  useEffect(load, [orderStatus]);

  return (
    <div>
      <h2>All Orders</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {["", "placed", "accepted", "preparing", "ready", "out_for_delivery", "delivered", "cancelled"].map((s) => (
          <button key={s} className="btn btn-sm" onClick={() => setOrderStatus(s)}
            style={{ background: orderStatus === s ? "var(--orange)" : "var(--white)", color: orderStatus === s ? "#fff" : "var(--ink)", border: "1px solid var(--gray-300)" }}>
            {s === "" ? "All" : s.replace("_", " ")}
          </button>
        ))}
      </div>
      {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 10 }}>Order</th><th>Customer</th><th>Restaurant</th><th>Amount</th><th>Payment</th><th>Status</th><th>Date</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 10 }}>#{o.id}</td>
                  <td>{o.customer_name}</td>
                  <td>{o.restaurant_name}</td>
                  <td>₹{o.total_amount}</td>
                  <td>{o.payment_method} · <span className={`badge ${o.payment_status === "paid" ? "badge-approved" : "badge-pending"}`}>{o.payment_status}</span></td>
                  <td style={{ textTransform: "capitalize" }}>{o.order_status.replace("_", " ")}</td>
                  <td>{new Date(o.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {orders.length === 0 && <div className="empty-state">No orders found.</div>}
        </div>
      )}
    </div>
  );
}

export function AdminPayments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [method, setMethod] = useState("");
  const [status, setStatus] = useState("");

  function load() {
    setLoading(true);
    adminListPayments({ method: method || undefined, status: status || undefined }).then((res) => setPayments(res.data)).finally(() => setLoading(false));
  }
  useEffect(load, [method, status]);

  return (
    <div>
      <h2>Payment Management</h2>
      <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
        <select className="input" style={{ maxWidth: 200 }} value={method} onChange={(e) => setMethod(e.target.value)}>
          <option value="">All Methods</option>
          <option value="razorpay">Razorpay</option>
          <option value="cod">Cash on Delivery</option>
          <option value="wallet">Wallet</option>
        </select>
        <select className="input" style={{ maxWidth: 200 }} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="success">Success</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
      </div>
      {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 10 }}>Order</th><th>Method</th><th>Amount</th><th>Status</th><th>Date</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 10 }}>#{p.order_id}</td>
                  <td>{p.method}</td>
                  <td>₹{p.amount}</td>
                  <td><span className={`badge ${p.status === "success" ? "badge-approved" : p.status === "failed" ? "badge-rejected" : "badge-pending"}`}>{p.status}</span></td>
                  <td>{new Date(p.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {payments.length === 0 && <div className="empty-state">No payments found.</div>}
        </div>
      )}
    </div>
  );
}
