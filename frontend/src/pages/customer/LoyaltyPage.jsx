import { useEffect, useState } from "react";
import { getMyLoyalty, getMyLoyaltyTransactions, getLoyaltyLevelsPublic } from "../../services/endpoints";
import { useAuthority } from "../../hooks/AuthorityContext";

const RANK_EMOJI = { Bronze: "🥉", Silver: "🥈", Gold: "🥇", Platinum: "💎", Diamond: "💠", Legends: "👑" };

export default function LoyaltyPage() {
  const { can, loaded } = useAuthority();
  const [summary, setSummary] = useState(null);
  const [txns, setTxns] = useState([]);
  const [levels, setLevels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loaded) return;
    if (!can("customer.loyalty")) { setLoading(false); return; }
    Promise.all([getMyLoyalty(), getMyLoyaltyTransactions(), getLoyaltyLevelsPublic()])
      .then(([s, t, l]) => { setSummary(s.data); setTxns(t.data); setLevels(l.data); })
      .catch((err) => setError(err.message || "Could not load loyalty information."))
      .finally(() => setLoading(false));
  }, [loaded, can]);

  if (loaded && !can("customer.loyalty")) {
    return (
      <div className="container" style={{ paddingTop: 40, maxWidth: 600 }}>
        <div className="empty-state">
          <h3>Loyalty program unavailable</h3>
          <p>Access to the Loyalty program has been restricted on your account by the administrator.</p>
        </div>
      </div>
    );
  }

  if (loading) return <div className="container" style={{ paddingTop: 30 }}><div className="skeleton" style={{ height: 260 }} /></div>;
  if (error) return <div className="container" style={{ paddingTop: 30 }}><div className="alert alert-error">{error}</div></div>;
  if (!summary) return null;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 820 }}>
      <h2>My Loyalty</h2>

      <div style={{
        background: "linear-gradient(135deg, var(--orange), var(--orange-dark))",
        borderRadius: 14, padding: 26, color: "#fff", marginBottom: 20,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div style={{ opacity: 0.85, fontSize: 14 }}>Current Rank</div>
            <div style={{ fontSize: 34, fontWeight: 700 }}>
              {RANK_EMOJI[summary.rank] || ""} {summary.rank}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ opacity: 0.85, fontSize: 14 }}>Points</div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{summary.points.toLocaleString()}</div>
          </div>
        </div>

        {summary.next_rank ? (
          <div style={{ marginTop: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6, opacity: 0.9 }}>
              <span>{summary.rank}</span>
              <span>{summary.points_needed_for_next_rank} points to {summary.next_rank}</span>
              <span>{summary.next_rank}</span>
            </div>
            <div style={{ background: "rgba(255,255,255,0.25)", borderRadius: 8, height: 12, overflow: "hidden" }}>
              <div style={{
                width: `${summary.progress_percent}%`, background: "#fff", height: "100%",
                borderRadius: 8, transition: "width 0.4s ease",
              }} />
            </div>
            <div style={{ fontSize: 12, opacity: 0.85, marginTop: 4 }}>{summary.progress_percent}% of the way there</div>
          </div>
        ) : (
          <div style={{ marginTop: 16, fontSize: 14, opacity: 0.9 }}>🎉 You've reached the highest rank!</div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12, marginBottom: 24 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 12.5, color: "var(--gray-500)", fontWeight: 700 }}>Lifetime Points</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{summary.lifetime_points.toLocaleString()}</div>
        </div>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 12.5, color: "var(--gray-500)", fontWeight: 700 }}>Total Orders</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>{summary.total_orders}</div>
        </div>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 12.5, color: "var(--gray-500)", fontWeight: 700 }}>Total Spending</div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>₹{summary.total_spending.toLocaleString()}</div>
        </div>
      </div>

      {summary.current_level_benefits && (
        <div className="card" style={{ padding: 18, marginBottom: 24, borderLeft: "4px solid var(--orange)" }}>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>Your {summary.rank} Benefits</div>
          <div style={{ color: "var(--gray-700)" }}>{summary.current_level_benefits}</div>
        </div>
      )}

      <h4>All Ranks</h4>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginBottom: 28 }}>
        {levels.map((l) => (
          <div key={l.id} className="card" style={{
            padding: 16, opacity: l.name === summary.rank ? 1 : 0.7,
            border: l.name === summary.rank ? "2px solid var(--orange)" : undefined,
          }}>
            <div style={{ fontWeight: 700 }}>{RANK_EMOJI[l.name] || ""} {l.name}</div>
            <div style={{ fontSize: 12.5, color: "var(--gray-500)", margin: "4px 0" }}>
              {l.minimum_points.toLocaleString()}{l.maximum_points != null ? ` – ${l.maximum_points.toLocaleString()}` : "+"} pts
            </div>
            <div style={{ fontSize: 13 }}>{l.benefits}</div>
          </div>
        ))}
      </div>

      <h4>Transaction History</h4>
      {txns.length === 0 ? (
        <div className="empty-state"><p>No loyalty activity yet. Place an order to start earning points!</p></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          {txns.map((t, idx) => (
            <div key={t.id} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: 14, borderBottom: idx < txns.length - 1 ? "1px solid var(--gray-100)" : "none",
            }}>
              <div>
                <div style={{ fontWeight: 700 }}>{t.description}</div>
                <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>{new Date(t.created_at).toLocaleString()}</div>
              </div>
              <div style={{ fontWeight: 700, color: t.points < 0 ? "var(--red)" : "var(--green)" }}>
                {t.points >= 0 ? "+" : ""}{t.points} pts
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
