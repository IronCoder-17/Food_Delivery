import { useEffect, useState } from "react";
import { getPromotionExperiments, createPromotionExperiment, setPromotionExperimentStatus } from "../../services/endpoints";

const STATUS_BADGE = { draft: "badge-pending", running: "badge-approved", completed: "badge-rejected" };

const emptyForm = { name: "", variant_a_label: "Promotion A", variant_b_label: "Promotion B", discount_percent_a: 10, discount_percent_b: 15 };

export default function AdminPromotions() {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    getPromotionExperiments().then((res) => setExperiments(res.data)).finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createPromotionExperiment(form);
      setShowForm(false);
      setForm(emptyForm);
      load();
    } catch (err) {
      setError(err.message || "Failed to create experiment.");
    } finally {
      setSaving(false);
    }
  }

  async function handleStatusChange(id, status) {
    try {
      await setPromotionExperimentStatus(id, status);
      load();
    } catch (err) {
      window.alert(err.message);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>🧪 Promotion Experiments</h2>
        {!showForm && <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>+ New Experiment</button>}
      </div>
      <p style={{ color: "var(--gray-500)" }}>Only one experiment can run at a time. Assignment is deterministic per customer.</p>

      {showForm && (
        <form onSubmit={handleCreate} className="card" style={{ padding: 20, marginBottom: 20 }}>
          {error && <div className="alert alert-error">{error}</div>}
          <div className="field">
            <label>Experiment Name</label>
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="grid grid-2">
            <div className="field">
              <label>Variant A Label</label>
              <input className="input" value={form.variant_a_label} onChange={(e) => setForm({ ...form, variant_a_label: e.target.value })} />
            </div>
            <div className="field">
              <label>Variant B Label</label>
              <input className="input" value={form.variant_b_label} onChange={(e) => setForm({ ...form, variant_b_label: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-2">
            <div className="field">
              <label>Discount % — A</label>
              <input className="input" type="number" min="0" max="90" value={form.discount_percent_a}
                onChange={(e) => setForm({ ...form, discount_percent_a: e.target.value })} />
            </div>
            <div className="field">
              <label>Discount % — B</label>
              <input className="input" type="number" min="0" max="90" value={form.discount_percent_b}
                onChange={(e) => setForm({ ...form, discount_percent_b: e.target.value })} />
            </div>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : "Create (Draft)"}</button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="skeleton" style={{ height: 250 }} />
      ) : (
        experiments.map((exp) => (
          <div key={exp.id} className="card" style={{ padding: 18, marginBottom: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{exp.name}</strong>
              <span className={`badge ${STATUS_BADGE[exp.status]}`}>{exp.status}</span>
            </div>
            <div className="grid grid-2" style={{ marginTop: 12 }}>
              {["A", "B"].map((v) => {
                const s = exp.stats[v];
                return (
                  <div key={v} className="card" style={{ padding: 12, background: "var(--gray-50, #fafafa)" }}>
                    <div style={{ fontWeight: 600, fontSize: 13.5 }}>{s.label} ({s.discount_percent}% off)</div>
                    <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: 6 }}>
                      Exposed: {s.users_exposed} · Orders: {s.orders} · Conversion: {s.conversion_rate}%
                    </div>
                    <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>
                      Revenue: ₹{s.revenue} · AOV: ₹{s.average_order_value}
                    </div>
                  </div>
                );
              })}
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              {exp.status === "draft" && <button className="btn btn-primary btn-sm" onClick={() => handleStatusChange(exp.id, "running")}>Start</button>}
              {exp.status === "running" && <button className="btn btn-outline btn-sm" onClick={() => handleStatusChange(exp.id, "completed")}>Complete</button>}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
