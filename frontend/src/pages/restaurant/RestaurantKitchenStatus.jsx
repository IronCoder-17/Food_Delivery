import { useEffect, useState } from "react";
import { getOwnKitchenStatus, updateKitchenStatus } from "../../services/endpoints";

const STATUS_OPTIONS = [
  { value: "normal", label: "🟢 Normal", hint: "Kitchen is running as usual." },
  { value: "busy", label: "🟠 Busy", hint: "Slightly higher order volume than usual." },
  { value: "very_busy", label: "🟠 Very Busy", hint: "High order volume -- expect delays." },
  { value: "overloaded", label: "🔴 Temporarily Overloaded", hint: "Consider pausing new orders if this continues." },
];

export default function RestaurantKitchenStatus() {
  const [status, setStatus] = useState("normal");
  const [extraMinutes, setExtraMinutes] = useState(0);
  const [savedAt, setSavedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function load() {
    setLoading(true);
    getOwnKitchenStatus()
      .then((res) => {
        setStatus(res.data.status);
        setExtraMinutes(res.data.extra_minutes);
        setSavedAt(res.data.updated_at);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function handleSave(e) {
    e.preventDefault();
    setError(""); setSuccess("");
    setSaving(true);
    try {
      const res = await updateKitchenStatus({ status, extra_minutes: Number(extraMinutes) || 0 });
      setSavedAt(res.data.updated_at);
      setSuccess("Kitchen status updated. Customers will see this before checkout.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="spinner" />;

  return (
    <div style={{ maxWidth: 560 }}>
      <h2 style={{ marginTop: 0 }}>Live Kitchen Load</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Let customers know your current kitchen load before they check out. This directly affects
        the estimated delivery time shown on their order.
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSave} className="card" style={{ padding: 22 }}>
        <div className="field">
          <label>Current Status</label>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {STATUS_OPTIONS.map((opt) => (
              <label key={opt.value} style={{
                display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 8,
                border: "1px solid var(--gray-300)", cursor: "pointer",
                background: status === opt.value ? "var(--orange-light, #ffe8d6)" : "transparent",
              }}>
                <input type="radio" name="kitchen_status" checked={status === opt.value} onChange={() => setStatus(opt.value)} />
                <div>
                  <div style={{ fontWeight: 600 }}>{opt.label}</div>
                  <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>{opt.hint}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="field">
          <label>Estimated Additional Preparation Time (minutes)</label>
          <input
            className="input" type="number" min="0" value={extraMinutes}
            onChange={(e) => setExtraMinutes(e.target.value)}
            disabled={status === "normal"}
          />
          <p style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: 4 }}>
            Added on top of each dish's normal preparation time when we estimate delivery times.
            Set to 0 when things are back to normal.
          </p>
        </div>

        <button className="btn btn-primary" disabled={saving}>
          {saving ? <span className="spinner" /> : "Update Kitchen Status"}
        </button>
        {savedAt && (
          <p style={{ fontSize: 12, color: "var(--gray-500)", marginTop: 10 }}>
            Last updated: {new Date(savedAt).toLocaleString()}
          </p>
        )}
      </form>
    </div>
  );
}
