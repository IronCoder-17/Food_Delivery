import { useEffect, useState } from "react";
import {
  adminListCustomerAuthorities, adminGetCustomerAuthority, adminUpdateCustomerAuthority,
  adminListRestaurantAuthorities, adminGetRestaurantAuthority, adminUpdateRestaurantAuthority,
  adminListPermissions, adminAuthorityAuditLogs,
} from "../../services/endpoints";

export default function AdminAuthority() {
  const [tab, setTab] = useState("customers");
  return (
    <div>
      <h2>Authority Management</h2>
      <p style={{ color: "var(--gray-500)", marginTop: -8, marginBottom: 18 }}>
        Control exactly what customers and restaurants are allowed to access or perform.
        Changes take effect immediately, on both the UI and the backend API.
      </p>
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        <button className={`btn btn-sm ${tab === "customers" ? "btn-primary" : "btn-outline"}`} onClick={() => setTab("customers")}>Customer Authorities</button>
        <button className={`btn btn-sm ${tab === "restaurants" ? "btn-primary" : "btn-outline"}`} onClick={() => setTab("restaurants")}>Restaurant Authorities</button>
        <button className={`btn btn-sm ${tab === "audit" ? "btn-primary" : "btn-outline"}`} onClick={() => setTab("audit")}>Audit Log</button>
      </div>
      {tab === "customers" && <UserAuthorityTab userType="customer" />}
      {tab === "restaurants" && <UserAuthorityTab userType="restaurant" />}
      {tab === "audit" && <AuditLogTab />}
    </div>
  );
}

function Toggle({ checked, onChange, disabled }) {
  return (
    <button
      type="button"
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      style={{
        width: 44, height: 24, borderRadius: 12, border: "none", cursor: disabled ? "default" : "pointer",
        background: checked ? "var(--green)" : "var(--gray-300)", position: "relative", flexShrink: 0,
        transition: "background 0.2s",
      }}
      aria-pressed={checked}
    >
      <span style={{
        position: "absolute", top: 3, left: checked ? 23 : 3, width: 18, height: 18,
        borderRadius: "50%", background: "#fff", transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
      }} />
    </button>
  );
}

function UserAuthorityTab({ userType }) {
  const isCustomer = userType === "customer";
  const listFn = isCustomer ? adminListCustomerAuthorities : adminListRestaurantAuthorities;
  const getFn = isCustomer ? adminGetCustomerAuthority : adminGetRestaurantAuthority;
  const updateFn = isCustomer ? adminUpdateCustomerAuthority : adminUpdateRestaurantAuthority;

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [permissions, setPermissions] = useState([]);
  const [selected, setSelected] = useState(null); // {id, name, email, authorities}
  const [pendingConfirm, setPendingConfirm] = useState(null); // {key, name, newValue}
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  function load() {
    setLoading(true);
    listFn({ search: search || undefined }).then((res) => setUsers(res.data)).finally(() => setLoading(false));
  }
  useEffect(() => {
    load();
    adminListPermissions(userType).then((res) => setPermissions(res.data));
  }, [userType]); // eslint-disable-line react-hooks/exhaustive-deps

  async function openUser(id) {
    const res = await getFn(id);
    setSelected({ id, ...res.data });
    setSaveError("");
  }

  function requestToggle(perm, currentValue) {
    setPendingConfirm({ key: perm.permission_key, name: perm.permission_name, newValue: !currentValue });
    setReason("");
  }

  async function confirmToggle() {
    if (!pendingConfirm) return;
    setSaving(true);
    setSaveError("");
    try {
      await updateFn(selected.id, pendingConfirm.key, pendingConfirm.newValue, reason || undefined);
      const res = await getFn(selected.id);
      setSelected({ id: selected.id, ...res.data });
      setPendingConfirm(null);
    } catch (err) {
      setSaveError(err.message || "Could not update this permission.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: selected ? "300px 1fr" : "1fr", gap: 18 }}>
      <div>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <input className="input" placeholder={`Search ${userType}s...`} value={search}
            onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
          <button className="btn btn-outline btn-sm" onClick={load}>Go</button>
        </div>
        {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
          <div className="card" style={{ padding: 0, overflow: "hidden", maxHeight: 520, overflowY: "auto" }}>
            {users.map((u) => (
              <button
                key={u.id}
                onClick={() => openUser(u.id)}
                style={{
                  display: "block", width: "100%", textAlign: "left", padding: 12, border: "none",
                  borderBottom: "1px solid var(--gray-100)", cursor: "pointer",
                  background: selected?.id === u.id ? "var(--orange-light)" : "#fff",
                }}
              >
                <div style={{ fontWeight: 700 }}>{u.name}</div>
                <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>{u.email}</div>
              </button>
            ))}
            {users.length === 0 && <div className="empty-state">No {userType}s found.</div>}
          </div>
        )}
      </div>

      {selected && (
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ marginTop: 0 }}>{selected.name}</h3>
          <p style={{ color: "var(--gray-500)", marginTop: -8 }}>{selected.email}</p>

          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 10 }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--gray-100)" }}>
                <th style={{ padding: "8px 4px" }}>Authority</th>
                <th style={{ padding: "8px 4px" }}>Description</th>
                <th style={{ padding: "8px 4px", textAlign: "right" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {permissions.map((p) => {
                const value = !!selected.authorities[p.permission_key];
                return (
                  <tr key={p.permission_key} style={{ borderBottom: "1px solid var(--gray-100)" }}>
                    <td style={{ padding: "10px 4px", fontWeight: 600 }}>{p.permission_name}</td>
                    <td style={{ padding: "10px 4px", fontSize: 13, color: "var(--gray-500)" }}>{p.description}</td>
                    <td style={{ padding: "10px 4px", textAlign: "right" }}>
                      <Toggle checked={value} onChange={() => requestToggle(p, value)} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {pendingConfirm && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 60 }}>
          <div className="card" style={{ padding: 22, maxWidth: 420, width: "90%" }}>
            <h4 style={{ marginTop: 0 }}>
              {pendingConfirm.newValue ? "Enable" : "Disable"} "{pendingConfirm.name}"?
            </h4>
            <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
              {pendingConfirm.newValue
                ? `This will restore ${selected.name}'s access to this feature immediately.`
                : `This will immediately restrict ${selected.name} from using this feature, on both the app UI and the backend API.`}
            </p>
            <input
              className="input" placeholder="Reason (optional but recommended)"
              value={reason} onChange={(e) => setReason(e.target.value)}
              style={{ marginBottom: 12 }}
            />
            {saveError && <div className="alert alert-error" style={{ padding: 8, fontSize: 13, marginBottom: 10 }}>{saveError}</div>}
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setPendingConfirm(null)} disabled={saving}>Cancel</button>
              <button
                className={`btn btn-sm ${pendingConfirm.newValue ? "btn-primary" : "btn-primary"}`}
                style={!pendingConfirm.newValue ? { background: "var(--red)", borderColor: "var(--red)" } : undefined}
                onClick={confirmToggle}
                disabled={saving}
              >
                {saving ? "Saving..." : pendingConfirm.newValue ? "Enable Permission" : "Disable Permission"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AuditLogTab() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    adminAuthorityAuditLogs().then((res) => setLogs(res.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="skeleton" style={{ height: 300 }} />;

  return (
    <div className="card" style={{ padding: 0, overflow: "hidden" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
            <th style={{ padding: 12 }}>When</th><th>Admin</th><th>User Type</th><th>User ID</th>
            <th>Permission</th><th>Change</th><th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((l) => (
            <tr key={l.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
              <td style={{ padding: 12, fontSize: 12.5 }}>{new Date(l.created_at).toLocaleString()}</td>
              <td>{l.admin_name}</td>
              <td style={{ textTransform: "capitalize" }}>{l.user_type}</td>
              <td>#{l.user_id}</td>
              <td>{l.permission}</td>
              <td>
                <span className={`badge ${l.previous_status ? "badge-approved" : "badge-rejected"}`}>{l.previous_status ? "ON" : "OFF"}</span>
                {" → "}
                <span className={`badge ${l.new_status ? "badge-approved" : "badge-rejected"}`}>{l.new_status ? "ON" : "OFF"}</span>
              </td>
              <td style={{ fontSize: 13 }}>{l.reason || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {logs.length === 0 && <div className="empty-state">No authority changes recorded yet.</div>}
    </div>
  );
}
