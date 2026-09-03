import { useEffect, useState } from "react";
import { getAdminDisputes, getAdminDispute, setAdminDisputeStatus, resolveAdminDispute } from "../../services/endpoints";

const STATUS_BADGE = {
  open: "badge-pending", under_review: "badge-pending", waiting_for_restaurant: "badge-pending",
  resolved: "badge-approved", rejected: "badge-rejected",
};
const STATUSES = ["open", "under_review", "waiting_for_restaurant", "resolved", "rejected"];

export default function AdminDisputes() {
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState(null);
  const [resolveForm, setResolveForm] = useState({ refund_amount: "", resolution_note: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    setLoading(true);
    getAdminDisputes(filter || undefined).then((res) => setDisputes(res.data)).finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps

  function openDetail(id) {
    getAdminDispute(id).then((res) => { setSelected(res.data); setResolveForm({ refund_amount: "", resolution_note: "" }); });
  }

  async function handleStatusChange(status) {
    setBusy(true);
    try {
      const res = await setAdminDisputeStatus(selected.id, status);
      setSelected(res.data);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleResolve(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await resolveAdminDispute(selected.id, {
        refund_amount: resolveForm.refund_amount ? parseFloat(resolveForm.refund_amount) : null,
        resolution_note: resolveForm.resolution_note,
      });
      setSelected(res.data);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (selected) {
    return (
      <div>
        <button className="btn btn-ghost btn-sm" onClick={() => setSelected(null)}>← All Disputes</button>
        <h2>Dispute #{selected.id}</h2>
        {error && <div className="alert alert-error">{error}</div>}

        <div className="card" style={{ padding: 16 }}>
          <div><strong>Customer:</strong> {selected.customer_name}</div>
          <div><strong>Restaurant:</strong> {selected.restaurant_name}</div>
          <div><strong>Order:</strong> #{selected.order_id}</div>
          <div><strong>Reason:</strong> {selected.reason}</div>
          <div><strong>Description:</strong> {selected.description || "—"}</div>
          <div style={{ marginTop: 8 }}><span className={`badge ${STATUS_BADGE[selected.status]}`}>{selected.status}</span></div>
        </div>

        {!["resolved", "rejected"].includes(selected.status) && (
          <div className="card" style={{ padding: 16, marginTop: 16 }}>
            <strong>Update Status</strong>
            <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
              {STATUSES.filter((s) => !["resolved", "rejected"].includes(s)).map((s) => (
                <button key={s} className="btn btn-outline btn-sm" disabled={busy} onClick={() => handleStatusChange(s)}>{s}</button>
              ))}
            </div>

            <form onSubmit={handleResolve} style={{ marginTop: 16 }}>
              <strong>Resolve</strong>
              <div className="field">
                <label>Refund Amount (₹, optional)</label>
                <input className="input" type="number" min="0" value={resolveForm.refund_amount}
                  onChange={(e) => setResolveForm({ ...resolveForm, refund_amount: e.target.value })} />
              </div>
              <div className="field">
                <label>Resolution Note</label>
                <textarea className="input" rows={2} value={resolveForm.resolution_note}
                  onChange={(e) => setResolveForm({ ...resolveForm, resolution_note: e.target.value })} />
              </div>
              <button className="btn btn-primary" disabled={busy}>Resolve &amp; Refund</button>
              <button type="button" className="btn btn-ghost" style={{ marginLeft: 8 }} disabled={busy} onClick={() => handleStatusChange("rejected")}>Reject</button>
            </form>
          </div>
        )}

        <div className="card" style={{ padding: 16, marginTop: 16 }}>
          <strong>Audit Log</strong>
          {selected.events.map((e, i) => (
            <div key={i} style={{ fontSize: 13, padding: "4px 0", borderTop: i > 0 ? "1px solid var(--gray-100)" : "none" }}>
              [{new Date(e.created_at).toLocaleString()}] {e.actor_type} — {e.event_type}: {e.note}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2>⚖️ Dispute Resolution</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["", ...STATUSES].map((s) => (
          <button key={s} className={`btn btn-sm ${filter === s ? "btn-primary" : "btn-outline"}`} onClick={() => setFilter(s)}>{s || "All"}</button>
        ))}
      </div>
      {loading ? (
        <div className="skeleton" style={{ height: 250 }} />
      ) : disputes.length === 0 ? (
        <div className="empty-state"><h3>No disputes</h3></div>
      ) : (
        disputes.map((d) => (
          <div key={d.id} className="card" style={{ padding: 14, marginBottom: 10, cursor: "pointer" }} onClick={() => openDetail(d.id)}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span><strong>#{d.id}</strong> — {d.customer_name} vs {d.restaurant_name}</span>
              <span className={`badge ${STATUS_BADGE[d.status]}`}>{d.status}</span>
            </div>
            <div style={{ fontSize: 13, color: "var(--gray-500)" }}>{d.reason} · Order #{d.order_id}</div>
          </div>
        ))
      )}
    </div>
  );
}
