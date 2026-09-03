import { useEffect, useState } from "react";
import { getFraudFlags, runFraudScan, setFraudFlagStatus } from "../../services/endpoints";

const STATUS_BADGE = { review: "badge-pending", warning: "badge-pending", restricted: "badge-rejected", cleared: "badge-approved" };
const RULE_LABELS = {
  repeated_cod_cancellations: "Repeated COD Cancellations",
  excessive_cancellations: "Excessive Cancellations",
  frequent_failed_payments: "Frequent Failed Payments",
  referral_abuse_pattern: "Referral Abuse Pattern",
  repeated_disputes: "Repeated Disputes",
  shared_address_multi_account: "Shared Address (Multi-Account)",
};

export default function AdminFraudCenter() {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    getFraudFlags(filter || undefined)
      .then((res) => setFlags(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleScan() {
    setScanning(true);
    setError("");
    try {
      const res = await runFraudScan();
      setFlags(res.data.flags);
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  }

  async function handleStatusChange(flagId, status) {
    try {
      await setFraudFlagStatus(flagId, status);
      load();
    } catch (err) {
      window.alert(err.message);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2 style={{ margin: 0 }}>🛡️ Fraud & Risk Center</h2>
          <p style={{ color: "var(--gray-500)", margin: "4px 0 0" }}>
            Rule-based pattern detection for human review -- not proof of fraud. Restrictions apply immediately via Authority Management.
          </p>
        </div>
        <button className="btn btn-primary" disabled={scanning} onClick={handleScan}>{scanning ? "Scanning..." : "Run Scan"}</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div style={{ display: "flex", gap: 8, margin: "16px 0" }}>
        {["", "review", "warning", "restricted", "cleared"].map((s) => (
          <button key={s} className={`btn btn-sm ${filter === s ? "btn-primary" : "btn-outline"}`} onClick={() => setFilter(s)}>
            {s || "All"}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 250 }} />
      ) : flags.length === 0 ? (
        <div className="empty-state"><h3>No flags</h3><p>Run a scan to check for suspicious patterns.</p></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Customer</th><th>Rule</th><th>Reason</th><th>Risk</th><th>Status</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {flags.map((f) => (
                <tr key={f.id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{f.customer_name}</td>
                  <td style={{ fontSize: 13 }}>{RULE_LABELS[f.rule] || f.rule}</td>
                  <td style={{ fontSize: 12.5, maxWidth: 260 }}>{f.reason}</td>
                  <td>
                    <span style={{
                      fontWeight: 700, color: f.risk_score >= 70 ? "var(--red)" : f.risk_score >= 40 ? "#f5a623" : "var(--gray-500)",
                    }}>
                      {f.risk_score}
                    </span>
                  </td>
                  <td><span className={`badge ${STATUS_BADGE[f.status]}`}>{f.status}</span></td>
                  <td>
                    <select className="input" style={{ padding: "4px 8px", fontSize: 13 }} value={f.status}
                      onChange={(e) => handleStatusChange(f.id, e.target.value)}>
                      <option value="review">Review</option>
                      <option value="warning">Warning</option>
                      <option value="restricted">Restricted</option>
                      <option value="cleared">Cleared</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
