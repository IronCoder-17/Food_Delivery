import { useEffect, useState } from "react";
import { getLiveSurplusDeals, addToCart as addToCartApi } from "../../services/endpoints";
import { useCart } from "../../hooks/CartContext";

function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

function formatCountdown(msRemaining) {
  if (msRemaining <= 0) return "Ended";
  const totalSeconds = Math.floor(msRemaining / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export default function SurplusDealsPage() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [addingId, setAddingId] = useState(null);
  const { refreshCart } = useCart();
  const now = useNow();

  function load() {
    setLoading(true);
    getLiveSurplusDeals()
      .then((res) => setDeals(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  async function handleAdd(deal) {
    if (addingId) return;
    setAddingId(deal.id);
    setError("");
    try {
      await addToCartApi(deal.food_id, 1);
      await refreshCart();
      setToast(`Added "${deal.food_name}" at the surplus price!`);
      setTimeout(() => setToast(""), 2500);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setAddingId(null);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <h2 style={{ marginTop: 0 }}>♻️ Surplus Deals</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Restaurant-listed surplus food at a discount. The restaurant is responsible for the
        safety and freshness of this food.
      </p>

      {toast && <div className="alert alert-success">{toast}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="grid grid-4">{[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 210 }} />)}</div>
      ) : deals.length === 0 ? (
        <div className="empty-state"><h3>No surplus deals right now</h3><p>Check back soon.</p></div>
      ) : (
        <div className="grid grid-4">
          {deals.map((d) => {
            const remainingMs = new Date(d.expiry_time).getTime() - now;
            const soldOut = d.remaining_quantity <= 0;
            return (
              <div key={d.id} className="card" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
                <div style={{ height: 130, background: "var(--orange-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, position: "relative" }}>
                  {d.food_image_url ? <img src={d.food_image_url} alt={d.food_name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "♻️"}
                  <span style={{ position: "absolute", top: 8, left: 8, background: "#2e7d32", color: "#fff", fontSize: 11.5, fontWeight: 700, padding: "3px 8px", borderRadius: 6 }}>
                    -{d.discount_percent}%
                  </span>
                </div>
                <div style={{ padding: 14, flex: 1, display: "flex", flexDirection: "column" }}>
                  <h4 style={{ margin: "0 0 2px" }}>{d.food_name}</h4>
                  <div style={{ fontSize: 13, color: "var(--gray-500)", marginBottom: 6 }}>{d.restaurant_name}</div>
                  <div style={{ fontSize: 13, marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, fontSize: 17 }}>₹{d.discount_price}</span>{" "}
                    <span style={{ textDecoration: "line-through", color: "var(--gray-500)" }}>₹{d.original_price}</span>
                  </div>
                  <div style={{ fontSize: 12.5, color: soldOut ? "var(--red)" : "var(--gray-700)" }}>
                    {soldOut ? "Sold out" : `${d.remaining_quantity} left`}
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginBottom: 10 }}>
                    ⏱ Order within {formatCountdown(remainingMs)}
                  </div>
                  <button className="btn btn-primary btn-sm" disabled={soldOut || addingId === d.id} onClick={() => handleAdd(d)}>
                    {addingId === d.id ? <span className="spinner" /> : soldOut ? "Sold out" : "Add +"}
                  </button>
                  <p style={{ fontSize: 10.5, color: "var(--gray-500)", marginTop: 8 }}>{d.safety_disclaimer}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}