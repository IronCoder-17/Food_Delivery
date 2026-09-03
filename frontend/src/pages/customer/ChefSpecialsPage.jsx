import { useEffect, useState } from "react";
import { getLiveChefSpecials, addToCart as addToCartApi } from "../../services/endpoints";
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
  const s = totalSeconds % 60;
  return h > 0 ? `${h}h ${m}m ${s}s` : `${m}m ${s}s`;
}

export default function ChefSpecialsPage() {
  const [specials, setSpecials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [addingId, setAddingId] = useState(null);
  const { refreshCart } = useCart();
  const now = useNow();

  function load() {
    setLoading(true);
    getLiveChefSpecials()
      .then((res) => setSpecials(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  async function handleAdd(special) {
    if (addingId) return; // prevent duplicate rapid clicks
    setAddingId(special.id);
    setError("");
    try {
      await addToCartApi(special.food_id, 1);
      await refreshCart();
      setToast(`Added "${special.food_name}" at the Chef's Special price!`);
      setTimeout(() => setToast(""), 2500);
      load(); // refresh remaining quantity
    } catch (err) {
      setError(err.message);
    } finally {
      setAddingId(null);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <h2 style={{ marginTop: 0 }}>👨‍🍳 Chef's Specials</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Limited-time, limited-quantity dishes at a special price -- first come, first served.
      </p>

      {toast && <div className="alert alert-success">{toast}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="grid grid-4">
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 220 }} />)}
        </div>
      ) : specials.length === 0 ? (
        <div className="empty-state"><h3>No Chef's Specials right now</h3><p>Check back soon for limited-time deals.</p></div>
      ) : (
        <div className="grid grid-4">
          {specials.map((s) => {
            const remainingMs = new Date(s.end_time).getTime() - now;
            const soldOut = s.remaining_quantity <= 0;
            return (
              <div key={s.id} className="card" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
                <div style={{ height: 140, background: "var(--orange-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, position: "relative" }}>
                  {s.food_image_url ? <img src={s.food_image_url} alt={s.food_name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "👨‍🍳"}
                  <span style={{ position: "absolute", top: 8, left: 8, background: "#7b2cbf", color: "#fff", fontSize: 11.5, fontWeight: 700, padding: "3px 8px", borderRadius: 6 }}>
                    🔥 Chef's Special
                  </span>
                </div>
                <div style={{ padding: 14, flex: 1, display: "flex", flexDirection: "column" }}>
                  <h4 style={{ margin: "0 0 2px" }}>{s.food_name}</h4>
                  <div style={{ fontSize: 13, color: "var(--gray-500)", marginBottom: 6 }}>{s.restaurant_name}</div>
                  {s.description && <p style={{ fontSize: 13, color: "var(--gray-700)", flex: 1 }}>{s.description}</p>}
                  <div style={{ fontSize: 13, marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, fontSize: 17 }}>₹{s.special_price}</span>{" "}
                    <span style={{ textDecoration: "line-through", color: "var(--gray-500)" }}>₹{s.original_price}</span>
                  </div>
                  <div style={{ fontSize: 12.5, color: soldOut ? "var(--red)" : "var(--gray-700)", marginBottom: 4 }}>
                    {soldOut ? "Sold out" : `${s.remaining_quantity} left`}
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginBottom: 10 }}>
                    ⏱ Ends in {formatCountdown(remainingMs)}
                  </div>
                  <button className="btn btn-primary btn-sm" disabled={soldOut || addingId === s.id} onClick={() => handleAdd(s)}>
                    {addingId === s.id ? <span className="spinner" /> : soldOut ? "Sold out" : "Add +"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}