import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getOrderTracking } from "../../services/endpoints";

const STAGE_LABELS = {
  placed: "Placed", accepted: "Accepted", preparing: "Preparing", ready: "Ready",
  out_for_delivery: "Out for Delivery", delivered: "Delivered", cancelled: "Cancelled",
};
const STAGE_ICONS = {
  placed: "🧾", accepted: "✅", preparing: "👨‍🍳", ready: "📦", out_for_delivery: "🛵", delivered: "🏠", cancelled: "✕",
};

export default function OrderTrackingPage() {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [track, setTrack] = useState(null);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback((manual = false) => {
    if (manual) setRefreshing(true);
    getOrderTracking(orderId)
      .then((res) => {
        setTrack(res.data);
        setLastUpdated(new Date());
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => { if (manual) setRefreshing(false); });
  }, [orderId]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, [load]);

  if (error) {
    return (
      <div className="container" style={{ paddingTop: 24 }}>
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate("/orders")}>← Back to Orders</button>
      </div>
    );
  }
  if (!track) return <div className="container" style={{ paddingTop: 24 }}><div className="skeleton" style={{ height: 300 }} /></div>;

  const isCancelled = track.order_status === "cancelled";
  const currentIndex = track.stage_order.indexOf(track.order_status);

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 640 }}>
      <button className="btn btn-ghost btn-sm" onClick={() => navigate("/orders")}>← Back to Orders</button>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginTop: 8 }}>
        <div>
          <h2 style={{ margin: 0 }}>Order #{track.order_id}</h2>
          <div style={{ fontSize: 14, color: "var(--gray-500)" }}>{track.restaurant_name}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <button className="btn btn-outline btn-sm" disabled={refreshing} onClick={() => load(true)}>
            {refreshing ? "Refreshing..." : "🔄 Refresh"}
          </button>
          {lastUpdated && (
            <div style={{ fontSize: 11, color: "var(--gray-500)", marginTop: 4 }}>
              🟢 Live — updated {lastUpdated.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {track.order_status === "placed" && (
        <div className="alert alert-warning" style={{ marginTop: 12, fontSize: 13.5 }}>
          Waiting for the restaurant to accept this order. This page updates automatically every few seconds —
          no action needed on your end.
        </div>
      )}

      {!isCancelled && (
        <div className="card" style={{ padding: 20, marginTop: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            {track.stage_order.map((stage, idx) => (
              <div key={stage} style={{ textAlign: "center", flex: 1, opacity: idx <= currentIndex ? 1 : 0.35 }}>
                <div style={{
                  fontSize: 20, width: 36, height: 36, borderRadius: "50%", margin: "0 auto 6px",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  background: idx <= currentIndex ? "var(--orange)" : "var(--gray-100)",
                  color: idx <= currentIndex ? "#fff" : "var(--gray-500)",
                }}>
                  {STAGE_ICONS[stage]}
                </div>
                <div style={{ fontSize: 10.5 }}>{STAGE_LABELS[stage]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {isCancelled && (
        <div className="alert alert-error" style={{ marginTop: 16 }}>This order was cancelled.</div>
      )}

      {track.estimated_delivery_time && (
        <div className="card" style={{ padding: 16, marginTop: 16, textAlign: "center" }}>
          <div style={{ fontSize: 13, color: "var(--gray-500)" }}>Estimated Delivery</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {new Date(track.estimated_delivery_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </div>
        </div>
      )}

      <div className="card" style={{ padding: 16, marginTop: 16 }}>
        <strong>Items</strong>
        {track.items.map((i, idx) => (
          <div key={idx} style={{ fontSize: 14, padding: "3px 0" }}>{i.food_name} × {i.quantity}</div>
        ))}
        <div style={{ fontSize: 13, color: "var(--gray-500)", marginTop: 8 }}>
          From: {track.restaurant_address}<br />To: {track.delivery_address}
        </div>
      </div>

      <div className="card" style={{ padding: 16, marginTop: 16 }}>
        <strong>Timeline</strong>
        {track.timeline.map((e, idx) => (
          <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5, padding: "5px 0", borderBottom: idx < track.timeline.length - 1 ? "1px solid var(--gray-100)" : "none" }}>
            <span>{STAGE_ICONS[e.status]} {STAGE_LABELS[e.status] || e.status}{e.note ? ` — ${e.note}` : ""}</span>
            <span style={{ color: "var(--gray-500)" }}>{new Date(e.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
          </div>
        ))}
      </div>
    </div>
  );
}