import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getMyOrders, cancelOrder, getReviewableItems, createReview, reorderOrder, previewOrderNutrition, logOrderNutrition, fetchPackingProofBlob } from "../../services/endpoints";
import { useAuthority } from "../../hooks/AuthorityContext";
import { useCart } from "../../hooks/CartContext";

const STATUS_STEPS = ["placed", "accepted", "preparing", "ready", "out_for_delivery", "delivered"];
const STATUS_LABELS = {
  placed: "Order Placed", accepted: "Accepted", preparing: "Preparing",
  ready: "Ready", out_for_delivery: "Out for Delivery", delivered: "Delivered", cancelled: "Cancelled",
};

function OrderTracker({ status }) {
  if (status === "cancelled") {
    return <div className="badge badge-rejected">Cancelled</div>;
  }
  const currentIdx = STATUS_STEPS.indexOf(status);
  return (
    <div style={{ display: "flex", alignItems: "center", marginTop: 10, marginBottom: 4 }}>
      {STATUS_STEPS.map((step, idx) => (
        <div key={step} style={{ display: "flex", alignItems: "center", flex: idx < STATUS_STEPS.length - 1 ? 1 : "none" }}>
          <div style={{
            width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
            background: idx <= currentIdx ? "var(--orange)" : "var(--gray-300)",
            display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 11, fontWeight: 700,
          }}>{idx <= currentIdx ? "✓" : ""}</div>
          {idx < STATUS_STEPS.length - 1 && (
            <div style={{ flex: 1, height: 3, background: idx < currentIdx ? "var(--orange)" : "var(--gray-300)" }} />
          )}
        </div>
      ))}
    </div>
  );
}

export default function OrdersPage() {
  const { can } = useAuthority();
  const { refreshCart } = useCart();
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [cancellingId, setCancellingId] = useState(null);
  const [cancelError, setCancelError] = useState("");
  const [reorderingId, setReorderingId] = useState(null);
  const [reorderSummary, setReorderSummary] = useState(null); // { orderId, added, unavailable }
  const [nutritionByOrder, setNutritionByOrder] = useState({}); // orderId -> preview data
  const [nutritionLoggedOrder, setNutritionLoggedOrder] = useState({}); // orderId -> true once logged
  const [packingProofUrls, setPackingProofUrls] = useState({}); // orderId -> object URL or "none" or "error"

  // key = `${order_id}:${food_id}` -> true if not yet reviewed
  const [reviewable, setReviewable] = useState({});
  const [reviewForm, setReviewForm] = useState(null); // { order_id, food_id, food_name, rating, comment }
  const [reviewSaving, setReviewSaving] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [reviewedJustNow, setReviewedJustNow] = useState({});

  function loadReviewable() {
    if (!can("customer.reviews")) return;
    getReviewableItems()
      .then((res) => {
        const map = {};
        res.data.forEach((item) => { map[`${item.order_id}:${item.food_id}`] = true; });
        setReviewable(map);
      })
      .catch(() => {});
  }

  useEffect(() => {
    let cancelled = false;

    function load(showSpinner) {
      if (showSpinner) setLoading(true);
      getMyOrders()
        .then((res) => { if (!cancelled) setOrders(res.data); })
        .finally(() => { if (!cancelled && showSpinner) setLoading(false); });
    }
    loadReviewable();

    // Initial load, then poll every 7s so orders that cross the 2-minute
    // auto-delivery mark (checked server-side on every fetch) update the
    // screen without the customer needing to refresh manually.
    load(true);
    const interval = setInterval(() => load(false), 7000);

    return () => { cancelled = true; clearInterval(interval); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handlePrint(order) {
    const w = window.open("", "_blank");
    w.document.write(`
      <html><head><title>Order #${order.id} Receipt</title>
      <style>body{font-family:'Times New Roman',serif;padding:30px;} h2{color:#E4602A;} table{width:100%;border-collapse:collapse;} td,th{padding:6px;border-bottom:1px solid #ddd;text-align:left;}</style>
      </head><body>
      <h2>QuickBite — Order Receipt</h2>
      <p><strong>Order #${order.id}</strong> · ${new Date(order.created_at).toLocaleString()}</p>
      <p>Restaurant: ${order.restaurant_name}<br/>Delivery Address: ${order.address}</p>
      <table><tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr>
      ${order.items.map((i) => `<tr><td>${i.food_name}</td><td>${i.quantity}</td><td>₹${i.unit_price}</td><td>₹${i.line_total}</td></tr>`).join("")}
      </table>
      <p>Subtotal: ₹${order.subtotal}<br/>Delivery Fee: ₹${order.delivery_fee}<br/><strong>Total: ₹${order.total_amount}</strong></p>
      <p>Payment: ${order.payment_method.toUpperCase()} (${order.payment_status})</p>
      </body></html>
    `);
    w.document.close();
    w.print();
  }

  async function handleCancel(orderId) {
    setCancelError("");
    setCancellingId(orderId);
    try {
      const res = await cancelOrder(orderId);
      setOrders((prev) => prev.map((o) => (o.id === orderId ? res.data : o)));
    } catch (err) {
      setCancelError(err.message || "Could not cancel this order.");
    } finally {
      setCancellingId(null);
    }
  }

  async function loadNutritionPreview(orderId) {
    if (nutritionByOrder[orderId]) return;
    try {
      const res = await previewOrderNutrition(orderId);
      setNutritionByOrder((prev) => ({ ...prev, [orderId]: res.data }));
    } catch {
      // No nutrition data available for this order -- fail silently, it's optional.
    }
  }

  async function handleLogNutrition(orderId) {
    try {
      await logOrderNutrition(orderId);
      setNutritionLoggedOrder((prev) => ({ ...prev, [orderId]: true }));
    } catch (err) {
      window.alert(err.message);
    }
  }

  async function loadPackingProof(orderId) {
    if (packingProofUrls[orderId]) return;
    try {
      const res = await fetchPackingProofBlob(orderId);
      const url = URL.createObjectURL(res.data);
      setPackingProofUrls((prev) => ({ ...prev, [orderId]: url }));
    } catch {
      setPackingProofUrls((prev) => ({ ...prev, [orderId]: "none" }));
    }
  }

  function toggleExpanded(orderId) {
    const next = expanded === orderId ? null : orderId;
    setExpanded(next);
    if (next) {
      loadNutritionPreview(orderId);
      loadPackingProof(orderId);
    }
  }

  function openReviewForm(order, item) {
    setReviewError("");
    setReviewForm({ order_id: order.id, food_id: item.food_id, food_name: item.food_name, rating: 5, comment: "" });
  }

  async function submitReview() {
    if (!reviewForm) return;
    setReviewError("");
    setReviewSaving(true);
    try {
      await createReview({
        order_id: reviewForm.order_id, food_id: reviewForm.food_id,
        rating: reviewForm.rating, comment: reviewForm.comment.trim() || undefined,
      });
      const key = `${reviewForm.order_id}:${reviewForm.food_id}`;
      setReviewable((prev) => { const next = { ...prev }; delete next[key]; return next; });
      setReviewedJustNow((prev) => ({ ...prev, [key]: true }));
      setReviewForm(null);
    } catch (err) {
      setReviewError(err.message || "Failed to submit review.");
    } finally {
      setReviewSaving(false);
    }
  }

  async function handleReorder(order) {
    setReorderingId(order.id);
    setReorderSummary(null);
    try {
      const res = await reorderOrder(order.id);
      await refreshCart();
      setReorderSummary({ orderId: order.id, ...res.data });
    } catch (err) {
      setReorderSummary({ orderId: order.id, added: [], unavailable: [], error: err.message });
    } finally {
      setReorderingId(null);
    }
  }

  if (loading) return <div className="container" style={{ paddingTop: 30 }}><div className="skeleton" style={{ height: 200 }} /></div>;

  if (orders.length === 0) {
    return (
      <div className="container" style={{ paddingTop: 60 }}>
        <div className="empty-state"><div style={{ fontSize: 42 }}>📦</div><h3>No orders yet</h3><p>Your order history will appear here.</p></div>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 800 }}>
      <h2>My Orders</h2>
      {cancelError && <div className="alert alert-error">{cancelError}</div>}
      {orders.map((order) => (
        <div key={order.id} className="card" style={{ padding: 18, marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
            <div>
              <div style={{ fontWeight: 700 }}>Order #{order.id} · {order.restaurant_name}</div>
              <div style={{ fontSize: 13, color: "var(--gray-500)" }}>{new Date(order.created_at).toLocaleString()}</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontWeight: 700, color: "var(--orange)" }}>₹{order.total_amount}</div>
              <span className={`badge ${order.payment_status === "paid" ? "badge-approved" : "badge-pending"}`}>{order.payment_status}</span>
            </div>
          </div>

          <OrderTracker status={order.order_status} />
          <div style={{ fontSize: 13, color: "var(--gray-500)", textTransform: "capitalize" }}>{STATUS_LABELS[order.order_status]}</div>

          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button className="btn btn-outline btn-sm" onClick={() => toggleExpanded(order.id)}>
              {expanded === order.id ? "Hide Details" : "View Details"}
            </button>
            {can("customer.track_order") && !["delivered", "cancelled"].includes(order.order_status) && (
              <button className="btn btn-outline btn-sm" onClick={() => navigate(`/orders/${order.id}/track`)}>📍 Track Order</button>
            )}
            <button className="btn btn-ghost btn-sm" onClick={() => handlePrint(order)}>Print Receipt</button>
            {can("customer.reorder") && order.order_status === "delivered" && (
              <button className="btn btn-outline btn-sm" disabled={reorderingId === order.id} onClick={() => handleReorder(order)}>
                {reorderingId === order.id ? "Adding..." : "🔁 Order Again"}
              </button>
            )}
            {can("customer.cancel_order") && ["placed", "accepted"].includes(order.order_status) && (
              <button
                className="btn btn-outline btn-sm"
                style={{ borderColor: "var(--red)", color: "var(--red)" }}
                onClick={() => handleCancel(order.id)}
                disabled={cancellingId === order.id}
              >
                {cancellingId === order.id ? "Cancelling..." : "Cancel Order"}
              </button>
            )}
          </div>

          {reorderSummary && reorderSummary.orderId === order.id && (
            <div className="card" style={{ padding: 12, marginTop: 10, background: "var(--gray-50, #fafafa)" }}>
              {reorderSummary.error && <div className="alert alert-error">{reorderSummary.error}</div>}
              {reorderSummary.added?.length > 0 && (
                <div style={{ fontSize: 13.5, color: "var(--green)", marginBottom: 4 }}>
                  ✓ Added to cart: {reorderSummary.added.map((a) => `${a.name} ×${a.quantity}`).join(", ")}
                </div>
              )}
              {reorderSummary.unavailable?.length > 0 && (
                <div style={{ fontSize: 13.5, color: "var(--red)" }}>
                  Unavailable: {reorderSummary.unavailable.map((u) => u.name).join(", ")} — these items are currently unavailable.
                </div>
              )}
              {reorderSummary.added?.length > 0 && (
                <button className="btn btn-primary btn-sm" style={{ marginTop: 8 }} onClick={() => navigate("/cart")}>Go to Cart</button>
              )}
            </div>
          )}

          {expanded === order.id && (
            <div style={{ marginTop: 12, borderTop: "1px solid var(--gray-100)", paddingTop: 12 }}>
              {order.items.map((i, idx) => {
                const key = `${order.id}:${i.food_id}`;
                const canReviewThis = order.order_status === "delivered" && can("customer.reviews") && reviewable[key];
                return (
                  <div key={idx} style={{ padding: "4px 0" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 14 }}>
                      <span>{i.food_name} × {i.quantity}</span>
                      <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        ₹{i.line_total}
                        {canReviewThis && (
                          <button className="btn btn-outline btn-sm" onClick={() => openReviewForm(order, i)}>
                            ⭐ Write a Review
                          </button>
                        )}
                        {reviewedJustNow[key] && <span style={{ fontSize: 12.5, color: "var(--green)" }}>✓ Reviewed</span>}
                      </span>
                    </div>

                    {reviewForm && reviewForm.order_id === order.id && reviewForm.food_id === i.food_id && (
                      <div className="card" style={{ padding: 14, marginTop: 8, background: "var(--gray-50, #fafafa)" }}>
                        {reviewError && <div className="alert alert-error">{reviewError}</div>}
                        <div style={{ fontWeight: 600, marginBottom: 6 }}>Rate {reviewForm.food_name}</div>
                        <div style={{ display: "flex", gap: 4, marginBottom: 10 }}>
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              key={star} type="button"
                              onClick={() => setReviewForm((f) => ({ ...f, rating: star }))}
                              style={{ background: "none", border: "none", cursor: "pointer", fontSize: 22, padding: 0, color: star <= reviewForm.rating ? "#f5a623" : "var(--gray-300)" }}
                            >★</button>
                          ))}
                        </div>
                        <textarea
                          className="input" rows={2} placeholder="Share your experience (optional)"
                          value={reviewForm.comment}
                          onChange={(e) => setReviewForm((f) => ({ ...f, comment: e.target.value }))}
                        />
                        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                          <button className="btn btn-primary btn-sm" disabled={reviewSaving} onClick={submitReview}>
                            {reviewSaving ? <span className="spinner" /> : "Submit Review"}
                          </button>
                          <button className="btn btn-ghost btn-sm" disabled={reviewSaving} onClick={() => setReviewForm(null)}>Cancel</button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
              <div style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 6 }}>Delivery to: {order.address}</div>
              {order.delivery_instruction && (
                <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>
                  Delivery instruction: {order.delivery_instruction.replace("_", " ")}
                </div>
              )}
              {(order.tip_amount > 0 || order.donation_amount > 0 || order.eco_delivery) && (
                <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: 2 }}>
                  {order.tip_amount > 0 && <span>Tip: ₹{order.tip_amount} </span>}
                  {order.donation_amount > 0 && <span>· Donation: ₹{order.donation_amount} </span>}
                  {order.eco_delivery && <span>· 🌱 Eco Delivery</span>}
                </div>
              )}

              {order.has_packing_proof && (
                <div style={{ marginTop: 10 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>📦 Packing Proof</div>
                  {packingProofUrls[order.id] && packingProofUrls[order.id] !== "none" ? (
                    <img src={packingProofUrls[order.id]} alt="Packing proof" style={{ maxWidth: 220, borderRadius: 8, border: "1px solid var(--gray-200)" }} />
                  ) : (
                    <div className="spinner" />
                  )}
                </div>
              )}

              {nutritionByOrder[order.id]?.has_nutrition_data && (
                <div className="card" style={{ padding: 12, marginTop: 10, background: "var(--gray-50, #fafafa)" }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Order Nutrition (estimate)</div>
                  <div style={{ fontSize: 13, color: "var(--gray-700)" }}>
                    {nutritionByOrder[order.id].calories} kcal · {nutritionByOrder[order.id].protein_grams}g protein ·{" "}
                    {nutritionByOrder[order.id].carbs_grams}g carbs · {nutritionByOrder[order.id].fat_grams}g fat
                  </div>
                  {nutritionLoggedOrder[order.id] ? (
                    <span style={{ fontSize: 12.5, color: "var(--green)" }}>✓ Added to your nutrition log</span>
                  ) : (
                    <button className="btn btn-outline btn-sm" style={{ marginTop: 8 }} onClick={() => handleLogNutrition(order.id)}>
                      Add to Nutrition Log
                    </button>
                  )}
                  <p style={{ fontSize: 10.5, color: "var(--gray-500)", marginTop: 6 }}>{nutritionByOrder[order.id].disclaimer}</p>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}