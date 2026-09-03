import { useEffect, useState } from "react";
import { getPassPlans, getMyPass, subscribeToPass, cancelPass } from "../../services/endpoints";

export default function QuickBitePassPage() {
  const [plans, setPlans] = useState([]);
  const [myPass, setMyPass] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([getPassPlans(), getMyPass()])
      .then(([plansRes, passRes]) => { setPlans(plansRes.data); setMyPass(passRes.data); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  async function handleSubscribe(planId) {
    setError("");
    setBusy(true);
    try {
      await subscribeToPass(planId);
      load();
    } catch (err) {
      setError(err.message || "Failed to subscribe.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCancel() {
    if (!confirm("Cancel your QuickBite Pass?")) return;
    setBusy(true);
    try {
      await cancelPass();
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <div className="container" style={{ paddingTop: 24 }}><div className="skeleton" style={{ height: 250 }} /></div>;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 720 }}>
      <h2>🚀 QuickBite Pass</h2>
      <p style={{ color: "var(--gray-500)", marginTop: 4 }}>
        Free delivery on eligible orders, up to a set number of times per period.
      </p>
      {error && <div className="alert alert-error">{error}</div>}

      {myPass?.is_currently_active ? (
        <div className="card" style={{ padding: 20, background: "linear-gradient(135deg, var(--orange), var(--orange-dark))", color: "#fff" }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{myPass.plan_name}</div>
          <div style={{ fontSize: 13.5, opacity: 0.9, marginTop: 4 }}>
            Active until {new Date(myPass.expires_at).toLocaleDateString()}
          </div>
          <div style={{ fontSize: 13.5, marginTop: 8 }}>
            Free deliveries used this period: {myPass.deliveries_used_in_period} / {myPass.max_free_deliveries_per_period}
          </div>
          <button className="btn btn-sm" style={{ background: "#fff", color: "var(--orange-dark)", marginTop: 12 }} disabled={busy} onClick={handleCancel}>
            Cancel Pass
          </button>
        </div>
      ) : (
        <div className="grid grid-2" style={{ marginTop: 16 }}>
          {plans.map((p) => (
            <div key={p.id} className="card" style={{ padding: 20 }}>
              <h3 style={{ margin: 0 }}>{p.name}</h3>
              <div style={{ fontSize: 26, fontWeight: 800, margin: "8px 0" }}>₹{p.price}<span style={{ fontSize: 13, fontWeight: 400, color: "var(--gray-500)" }}> / {p.duration_days} days</span></div>
              <ul style={{ fontSize: 13.5, color: "var(--gray-700)", paddingLeft: 18 }}>
                <li>Up to {p.max_free_deliveries_per_period} free deliveries per period</li>
                {p.min_order_amount > 0 && <li>Minimum order ₹{p.min_order_amount}</li>}
                {p.eligible_restaurant_ids.length > 0 && <li>Valid at select restaurants only</li>}
              </ul>
              <button className="btn btn-primary btn-block" disabled={busy} onClick={() => handleSubscribe(p.id)}>
                {busy ? "..." : "Subscribe (pays from Wallet)"}
              </button>
            </div>
          ))}
          {plans.length === 0 && <div className="empty-state"><h3>No plans available right now</h3></div>}
        </div>
      )}
    </div>
  );
}
