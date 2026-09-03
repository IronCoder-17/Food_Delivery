import { useEffect, useState } from "react";
import { getWallet, getWalletTransactions } from "../../services/endpoints";

export default function WalletPage() {
  const [wallet, setWallet] = useState(null);
  const [txns, setTxns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getWallet(), getWalletTransactions()])
      .then(([w, t]) => { setWallet(w.data); setTxns(t.data); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ paddingTop: 30 }}><div className="skeleton" style={{ height: 200 }} /></div>;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 700 }}>
      <h2>My Wallet</h2>

      <div style={{ background: "linear-gradient(135deg, var(--orange), var(--orange-dark))", borderRadius: 14, padding: 26, color: "#fff", marginBottom: 20 }}>
        <div style={{ opacity: 0.85, fontSize: 14 }}>Current Balance</div>
        <div style={{ fontSize: 38, fontWeight: 700 }}>₹{wallet.balance}</div>
        <div style={{ display: "flex", gap: 24, marginTop: 14, fontSize: 14 }}>
          <div>Total Credits<br /><strong>₹{wallet.total_credits}</strong></div>
          <div>Total Debits<br /><strong>₹{wallet.total_debits}</strong></div>
        </div>
      </div>

      <h4>Transaction History</h4>
      {txns.length === 0 ? (
        <div className="empty-state"><p>No wallet transactions yet. Play the GK Game to earn rewards!</p></div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          {txns.map((t, idx) => (
            <div key={t.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: 14, borderBottom: idx < txns.length - 1 ? "1px solid var(--gray-100)" : "none" }}>
              <div>
                <div style={{ fontWeight: 700 }}>{t.reason}</div>
                <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>{new Date(t.created_at).toLocaleString()}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontWeight: 700, color: t.type === "debit" ? "var(--red)" : "var(--green)" }}>
                  {t.type === "debit" ? "−" : "+"}₹{t.amount}
                </div>
                <div style={{ fontSize: 12, color: "var(--gray-500)" }}>Balance: ₹{t.balance_after}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
