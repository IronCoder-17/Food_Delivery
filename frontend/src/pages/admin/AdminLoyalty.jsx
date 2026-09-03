import { useEffect, useState } from "react";
import {
  adminListCustomerLoyalty, adminGetCustomerLoyalty, adminAdjustCustomerPoints,
  adminListLoyaltyLevels, adminUpdateLoyaltyLevel,
} from "../../services/endpoints";

const RANK_EMOJI = { Bronze: "🥉", Silver: "🥈", Gold: "🥇", Platinum: "💎", Diamond: "💠", Legends: "👑" };

export default function AdminLoyalty() {
  const [tab, setTab] = useState("customers");
  return (
    <div>
      <h2>Loyalty Management</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        <button className={`btn btn-sm ${tab === "customers" ? "btn-primary" : "btn-outline"}`} onClick={() => setTab("customers")}>Customers</button>
        <button className={`btn btn-sm ${tab === "levels" ? "btn-primary" : "btn-outline"}`} onClick={() => setTab("levels")}>Rank Configuration</button>
      </div>
      {tab === "customers" ? <CustomerLoyaltyTab /> : <LevelsTab />}
    </div>
  );
}

function CustomerLoyaltyTab() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [rankFilter, setRankFilter] = useState("");
  const [detail, setDetail] = useState(null);
  const [adjustDelta, setAdjustDelta] = useState("");
  const [adjustReason, setAdjustReason] = useState("");
  const [adjustError, setAdjustError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    adminListCustomerLoyalty({ search: search || undefined, rank: rankFilter || undefined })
      .then((res) => setRows(res.data))
      .finally(() => setLoading(false));
  }
  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function openDetail(customerId) {
    const res = await adminGetCustomerLoyalty(customerId);
    setDetail(res.data);
    setAdjustDelta("");
    setAdjustReason("");
    setAdjustError("");
  }

  async function submitAdjustment() {
    setAdjustError("");
    const delta = parseInt(adjustDelta, 10);
    if (!delta) { setAdjustError("Enter a non-zero number of points."); return; }
    if (!adjustReason.trim()) { setAdjustError("A reason is required."); return; }
    setSaving(true);
    try {
      await adminAdjustCustomerPoints(detail.customer_id, delta, adjustReason.trim());
      const res = await adminGetCustomerLoyalty(detail.customer_id);
      setDetail(res.data);
      setAdjustDelta("");
      setAdjustReason("");
      load();
    } catch (err) {
      setAdjustError(err.message || "Could not adjust points.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
        <input className="input" style={{ maxWidth: 260 }} placeholder="Search by name..." value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
        <select className="input" style={{ maxWidth: 160 }} value={rankFilter} onChange={(e) => setRankFilter(e.target.value)}>
          <option value="">All ranks</option>
          {Object.keys(RANK_EMOJI).map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <button className="btn btn-outline btn-sm" onClick={load}>Filter</button>
      </div>

      {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Name</th><th>Email</th><th>Orders</th><th>Spending</th>
                <th>Points</th><th>Rank</th><th>Updated</th><th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.customer_id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{c.name}</td>
                  <td>{c.email}</td>
                  <td>{c.total_orders}</td>
                  <td>₹{c.total_spending.toLocaleString()}</td>
                  <td>{c.points.toLocaleString()}</td>
                  <td>{RANK_EMOJI[c.rank] || ""} {c.rank}</td>
                  <td style={{ fontSize: 12.5, color: "var(--gray-500)" }}>{c.updated_at ? new Date(c.updated_at).toLocaleDateString() : "-"}</td>
                  <td><button className="btn btn-sm btn-ghost" onClick={() => openDetail(c.customer_id)}>Manage</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <div className="empty-state">No customers found.</div>}
        </div>
      )}

      {detail && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }} onClick={() => setDetail(null)}>
          <div className="card" style={{ padding: 24, maxWidth: 520, width: "90%", maxHeight: "85vh", overflow: "auto" }} onClick={(e) => e.stopPropagation()}>
            <h3>{detail.name}</h3>
            <p style={{ color: "var(--gray-500)" }}>{detail.email}</p>

            <div className="grid grid-2" style={{ marginBottom: 14, gap: 10 }}>
              <MiniStat label="Rank" value={`${RANK_EMOJI[detail.rank] || ""} ${detail.rank}`} />
              <MiniStat label="Points" value={detail.points.toLocaleString()} />
              <MiniStat label="Lifetime Points" value={detail.lifetime_points.toLocaleString()} />
              <MiniStat label="Total Orders" value={detail.total_orders} />
            </div>

            <div className="card" style={{ padding: 14, marginBottom: 16, background: "var(--gray-50)" }}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>Adjust Points</div>
              <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                <input className="input" style={{ maxWidth: 130 }} type="number" placeholder="e.g. 500 or -200"
                  value={adjustDelta} onChange={(e) => setAdjustDelta(e.target.value)} />
                <input className="input" style={{ flex: 1, minWidth: 180 }} placeholder="Reason (required)"
                  value={adjustReason} onChange={(e) => setAdjustReason(e.target.value)} />
              </div>
              {adjustError && <div className="alert alert-error" style={{ padding: 8, fontSize: 13 }}>{adjustError}</div>}
              <button className="btn btn-primary btn-sm" onClick={submitAdjustment} disabled={saving}>
                {saving ? "Saving..." : "Apply Adjustment"}
              </button>
            </div>

            <h4>Recent Transactions</h4>
            {detail.transactions.length === 0 ? (
              <p style={{ color: "var(--gray-500)" }}>No transactions yet.</p>
            ) : detail.transactions.slice(0, 15).map((t) => (
              <div key={t.id} style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5, padding: "6px 0", borderBottom: "1px solid var(--gray-100)" }}>
                <span>{t.description}</span>
                <span style={{ fontWeight: 700, color: t.points < 0 ? "var(--red)" : "var(--green)" }}>{t.points >= 0 ? "+" : ""}{t.points}</span>
              </div>
            ))}

            <button className="btn btn-ghost" onClick={() => setDetail(null)} style={{ marginTop: 14 }}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

function LevelsTab() {
  const [levels, setLevels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null); // level being edited
  const [form, setForm] = useState({});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");

  function load() {
    setLoading(true);
    adminListLoyaltyLevels().then((res) => setLevels(res.data)).finally(() => setLoading(false));
  }
  useEffect(load, []);

  function startEdit(level) {
    setEditing(level.id);
    setForm({
      name: level.name, minimum_points: level.minimum_points,
      maximum_points: level.maximum_points ?? "", benefits: level.benefits || "",
      description: level.description || "", is_active: level.is_active,
    });
    setError("");
    setNotice("");
  }

  async function save(levelId) {
    setError("");
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        minimum_points: parseInt(form.minimum_points, 10),
        maximum_points: form.maximum_points === "" ? null : parseInt(form.maximum_points, 10),
        benefits: form.benefits,
        description: form.description,
        is_active: form.is_active,
      };
      const res = await adminUpdateLoyaltyLevel(levelId, payload);
      setNotice(`Saved. ${res.data.customers_rank_recalculated} customer rank(s) recalculated.`);
      setEditing(null);
      load();
    } catch (err) {
      setError(err.message || "Could not save this rank.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="skeleton" style={{ height: 300 }} />;

  return (
    <div>
      {notice && <div className="alert alert-success" style={{ marginBottom: 14 }}>{notice}</div>}
      <div style={{ display: "grid", gap: 12 }}>
        {levels.map((l) => (
          <div key={l.id} className="card" style={{ padding: 18 }}>
            {editing === l.id ? (
              <div>
                <div className="grid grid-2" style={{ gap: 10, marginBottom: 10 }}>
                  <label>Name
                    <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                  </label>
                  <label>Active
                    <select className="input" value={form.is_active ? "1" : "0"} onChange={(e) => setForm({ ...form, is_active: e.target.value === "1" })}>
                      <option value="1">Active</option>
                      <option value="0">Inactive</option>
                    </select>
                  </label>
                  <label>Minimum Points
                    <input className="input" type="number" value={form.minimum_points} onChange={(e) => setForm({ ...form, minimum_points: e.target.value })} />
                  </label>
                  <label>Maximum Points (blank = unlimited)
                    <input className="input" type="number" value={form.maximum_points} onChange={(e) => setForm({ ...form, maximum_points: e.target.value })} />
                  </label>
                </div>
                <label style={{ display: "block", marginBottom: 10 }}>Benefits
                  <textarea className="input" rows={2} value={form.benefits} onChange={(e) => setForm({ ...form, benefits: e.target.value })} />
                </label>
                <label style={{ display: "block", marginBottom: 10 }}>Description
                  <textarea className="input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                </label>
                {error && <div className="alert alert-error" style={{ padding: 8, fontSize: 13, marginBottom: 10 }}>{error}</div>}
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-primary btn-sm" onClick={() => save(l.id)} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setEditing(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 17 }}>
                    {RANK_EMOJI[l.name] || ""} {l.name}
                    {!l.is_active && <span className="badge badge-rejected" style={{ marginLeft: 8 }}>Inactive</span>}
                  </div>
                  <div style={{ color: "var(--gray-500)", fontSize: 13.5, margin: "4px 0" }}>
                    {l.minimum_points.toLocaleString()}{l.maximum_points != null ? ` – ${l.maximum_points.toLocaleString()}` : "+"} points
                  </div>
                  <div style={{ fontSize: 14 }}>{l.benefits}</div>
                </div>
                <button className="btn btn-outline btn-sm" onClick={() => startEdit(l)}>Edit</button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return <div className="card" style={{ padding: 10 }}><div style={{ fontSize: 12, color: "var(--gray-500)" }}>{label}</div><div style={{ fontWeight: 700 }}>{value}</div></div>;
}
