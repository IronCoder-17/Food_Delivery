import { useEffect, useState } from "react";
import { getMyReferrals } from "../../services/endpoints";

export default function ReferralsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getMyReferrals().then((res) => setData(res.data)).catch((err) => setError(err.message));
  }, []);

  function copyCode() {
    if (!data) return;
    navigator.clipboard?.writeText(data.referral_code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  }

  const statusBadge = { pending: "badge-pending", completed: "badge-approved" };

  if (error) return <div className="container" style={{ paddingTop: 24 }}><div className="alert alert-error">{error}</div></div>;
  if (!data) return <div className="container" style={{ paddingTop: 24 }}><div className="skeleton" style={{ height: 200 }} /></div>;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 720 }}>
      <h2>🎁 Refer & Earn</h2>
      <p style={{ color: "var(--gray-500)", marginTop: 4 }}>
        Share your code. When a friend signs up and completes their first order, you both earn loyalty points.
      </p>

      {!data.rewards_active && (
        <div className="alert alert-error">Referral rewards are currently paused by the administrator, but you can still share your code.</div>
      )}

      <div className="card" style={{ padding: 24, textAlign: "center", background: "linear-gradient(135deg, var(--orange), var(--orange-dark))", color: "#fff" }}>
        <div style={{ fontSize: 13, opacity: 0.9 }}>Your Referral Code</div>
        <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: 1, margin: "8px 0" }}>{data.referral_code}</div>
        <button className="btn btn-sm" style={{ background: "#fff", color: "var(--orange-dark)" }} onClick={copyCode}>
          {copied ? "Copied!" : "Copy Code"}
        </button>
      </div>

      <div className="grid grid-3" style={{ marginTop: 20 }}>
        <div className="card" style={{ padding: 16, textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{data.total_referrals}</div>
          <div style={{ fontSize: 13, color: "var(--gray-500)" }}>Total Invites</div>
        </div>
        <div className="card" style={{ padding: 16, textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{data.completed_referrals}</div>
          <div style={{ fontSize: 13, color: "var(--gray-500)" }}>Completed</div>
        </div>
        <div className="card" style={{ padding: 16, textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{data.points_earned_from_referrals}</div>
          <div style={{ fontSize: 13, color: "var(--gray-500)" }}>Points Earned</div>
        </div>
      </div>

      <div style={{ fontSize: 13.5, color: "var(--gray-500)", margin: "16px 0" }}>
        You earn {data.referrer_reward_points} points per completed referral. Your friend earns {data.referred_reward_points} points on their first order.
      </div>

      <h4>Your Invites</h4>
      {data.referrals.length === 0 ? (
        <div className="empty-state"><h3>No invites yet</h3><p>Share your code with friends to get started.</p></div>
      ) : (
        data.referrals.map((r) => (
          <div key={r.id} className="card" style={{ padding: 14, marginBottom: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <strong>{r.referred_name}</strong>
              <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>Invited {new Date(r.created_at).toLocaleDateString()}</div>
            </div>
            <span className={`badge ${statusBadge[r.status] || ""}`}>{r.status}</span>
          </div>
        ))
      )}
    </div>
  );
}
