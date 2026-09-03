import { useEffect, useState } from "react";
import { getMyDisputes, getMyOrders, createDispute } from "../../services/endpoints";

const REASONS = [
  { value: "missing_item", label: "Missing Item" },
  { value: "wrong_item", label: "Wrong Item" },
  { value: "damaged_item", label: "Damaged Item" },
  { value: "payment_issue", label: "Payment Issue" },
  { value: "delivery_issue", label: "Delivery Issue" },
  { value: "other", label: "Other" },
];
const STATUS_BADGE = {
  open: "badge-pending", under_review: "badge-pending", waiting_for_restaurant: "badge-pending",
  resolved: "badge-approved", rejected: "badge-rejected",
};

export default function DisputesPage() {
  const [disputes, setDisputes] = useState([]);
  const [deliveredOrders, setDeliveredOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ order_id: "", reason: "missing_item", description: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([getMyDisputes(), getMyOrders()])
      .then(([disputesRes, ordersRes]) => {
        setDisputes(disputesRes.data);
        setDeliveredOrders(ordersRes.data.filter((o) => o.order_status === "delivered"));
      })
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  function openForm() {
    setError("");
    setForm({ order_id: deliveredOrders[0]?.id || "", reason: "missing_item", description: "" });
    setShowForm(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!form.order_id) { setError("Select an order."); return; }
    setSaving(true);
    try {
      await createDispute({ order_id: parseInt(form.order_id, 10), reason: form.reason, description: form.description });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message || "Failed to open dispute.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="container" style={{ paddingTop: 24 }}><div className="skeleton" style={{ height: 200 }} /></div>;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 700 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>⚖️ Order Disputes</h2>
        {!showForm && <button className="btn btn-primary btn-sm" disabled={deliveredOrders.length === 0} onClick={openForm}>+ Open Dispute</button>}
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="card" style={{ padding: 20, marginTop: 16 }}>
          {error && <div className="alert alert-error">{error}</div>}
          <div className="field">
            <label>Order</label>
            <select className="input" value={form.order_id} onChange={(e) => setForm({ ...form, order_id: e.target.value })}>
              {deliveredOrders.map((o) => <option key={o.id} value={o.id}>#{o.id} — {o.restaurant_name} (₹{o.total_amount})</option>)}
            </select>
          </div>
          <div className="field">
            <label>Reason</label>
            <select className="input" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })}>
              {REASONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>
          <div className="field">
            <label>Description</label>
            <textarea className="input" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Describe what happened" />
          </div>
          <button className="btn btn-primary" disabled={saving}>{saving ? "Submitting..." : "Submit Dispute"}</button>
          <button type="button" className="btn btn-ghost" style={{ marginLeft: 8 }} onClick={() => setShowForm(false)}>Cancel</button>
        </form>
      )}

      <div style={{ marginTop: 20 }}>
        {disputes.length === 0 ? (
          <div className="empty-state"><h3>No disputes</h3><p>Only delivered orders are eligible for a dispute.</p></div>
        ) : (
          disputes.map((d) => (
            <div key={d.id} className="card" style={{ padding: 16, marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>Order #{d.order_id} — {REASONS.find((r) => r.value === d.reason)?.label}</strong>
                <span className={`badge ${STATUS_BADGE[d.status]}`}>{d.status}</span>
              </div>
              {d.description && <div style={{ fontSize: 13.5, marginTop: 6 }}>{d.description}</div>}
              {d.resolution_note && (
                <div style={{ fontSize: 13.5, marginTop: 8, color: "var(--green)" }}>
                  Resolution: {d.resolution_note}{d.refund_amount ? ` (₹${d.refund_amount} refunded to wallet)` : ""}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
