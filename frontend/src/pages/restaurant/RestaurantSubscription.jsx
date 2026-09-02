import { useEffect, useState } from "react";
import { getAvailableSubscriptionPlans, getMySubscription, requestSubscription } from "../../services/endpoints";

const STATUS_BADGE = { pending: "badge-pending", active: "badge-approved", expired: "badge-rejected", cancelled: "badge-rejected" };

export default function RestaurantSubscription() {
  const [plans, setPlans] = useState([]);
  const [sub, setSub] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([getAvailableSubscriptionPlans(), getMySubscription()])
      .then(([plansRes, subRes]) => { setPlans(plansRes.data); setSub(subRes.data); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  async function handleRequest(planId) {
    setError("");
    setBusy(true);
    try {
      await requestSubscription(planId);
      load();
    } catch (err) {
      setError(err.message || "Failed to request subscription.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="skeleton" style={{ height: 250 }} />;

  return (
    <div>
      <h2>Subscription Plan</h2>
      <p style={{ color: "var(--gray-500)" }}>
        Unlock advanced analytics, promotional tools, and sponsored-placement eligibility.
      </p>
      {error && <div className="alert alert-error">{error}</div>}

      {sub && (
        <div className="card" style={{ padding: 16, marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <strong>{sub.plan_name}</strong>
            <span className={`badge ${STATUS_BADGE[sub.status]}`}>{sub.status}</span>
          </div>
          {sub.status === "pending" && (
            <div style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 6 }}>
              Awaiting admin approval. Once approved, your plan's features activate immediately.
            </div>
          )}
          {sub.status === "active" && (
            <div style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 6 }}>
              Active until {new Date(sub.expires_at).toLocaleDateString()}
            </div>
          )}
        </div>
      )}

      {(!sub || sub.status === "cancelled" || sub.status === "expired") && (
        <div className="grid grid-3">
          {plans.map((p) => (
            <div key={p.id} className="card" style={{ padding: 20 }}>
              <h4 style={{ margin: 0 }}>{p.name}</h4>
              <div style={{ fontSize: 22, fontWeight: 800, margin: "8px 0" }}>₹{p.price}<span style={{ fontSize: 12.5, fontWeight: 400, color: "var(--gray-500)" }}> / {p.duration_days}d</span></div>
              <p style={{ fontSize: 13, color: "var(--gray-700)" }}>{p.description}</p>
              <ul style={{ fontSize: 12.5, color: "var(--gray-700)", paddingLeft: 16 }}>
                {p.granted_permissions.map((perm) => <li key={perm}>{perm.replace("restaurant.", "").replace(/_/g, " ")}</li>)}
              </ul>
              <button className="btn btn-primary btn-block" disabled={busy} onClick={() => handleRequest(p.id)}>Request Plan</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
