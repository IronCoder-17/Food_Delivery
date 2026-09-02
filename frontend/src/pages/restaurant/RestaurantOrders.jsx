import { useEffect, useState, useRef } from "react";
import { getRestaurantOrders, updateOrderStatus, uploadPackingProof } from "../../services/endpoints";

const NEXT_STATUS = {
  placed: ["accepted", "cancelled"],
  accepted: ["preparing", "cancelled"],
  preparing: ["ready", "cancelled"],
  ready: ["out_for_delivery"],
  out_for_delivery: ["delivered"],
};
const LABELS = { accepted: "Accept", preparing: "Start Preparing", ready: "Mark Ready", out_for_delivery: "Out for Delivery", delivered: "Mark Delivered", cancelled: "Cancel" };

export default function RestaurantOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");
  const [uploadingId, setUploadingId] = useState(null);
  const fileInputRefs = useRef({});

  function load() {
    setLoading(true);
    getRestaurantOrders().then((res) => setOrders(res.data)).finally(() => setLoading(false));
  }
  useEffect(load, []);

  async function handleStatusChange(order, status) {
    try {
      await updateOrderStatus(order.id, status);
      load();
    } catch (err) {
      alert(err.message);
    }
  }

  async function handleUploadProof(order, file) {
    if (!file) return;
    setUploadingId(order.id);
    try {
      await uploadPackingProof(order.id, file);
      load();
    } catch (err) {
      alert(err.message);
    } finally {
      setUploadingId(null);
    }
  }

  const filtered = filter ? orders.filter((o) => o.order_status === filter) : orders;

  return (
    <div>
      <h2>Order Management</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {["", "placed", "accepted", "preparing", "ready", "out_for_delivery", "delivered", "cancelled"].map((s) => (
          <button key={s} className="btn btn-sm" onClick={() => setFilter(s)}
            style={{ background: filter === s ? "var(--orange)" : "var(--white)", color: filter === s ? "#fff" : "var(--ink)", border: "1px solid var(--gray-300)" }}>
            {s === "" ? "All" : s.replace("_", " ")}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 300 }} />
      ) : filtered.length === 0 ? (
        <div className="empty-state"><h3>No orders here</h3></div>
      ) : (
        filtered.map((order) => (
          <div key={order.id} className="card" style={{ padding: 18, marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
              <div>
                <div style={{ fontWeight: 700 }}>Order #{order.id} — {order.customer_name}</div>
                <div style={{ fontSize: 13, color: "var(--gray-500)" }}>{new Date(order.created_at).toLocaleString()}</div>
                <div style={{ fontSize: 13.5, marginTop: 4 }}>{order.items.map((i) => `${i.food_name} ×${i.quantity}`).join(", ")}</div>
                <div style={{ fontSize: 13, color: "var(--gray-500)", marginTop: 4 }}>Deliver to: {order.address}</div>
                {order.delivery_instruction && (
                  <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>
                    Instruction: {order.delivery_instruction.replace("_", " ")}
                  </div>
                )}
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontWeight: 700 }}>₹{order.total_amount}</div>
                <span className="badge badge-orange" style={{ textTransform: "capitalize" }}>{order.order_status.replace("_", " ")}</span>
                <div style={{ fontSize: 12, marginTop: 4, color: "var(--gray-500)" }}>{order.payment_method.toUpperCase()} · {order.payment_status}</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap", alignItems: "center" }}>
              {NEXT_STATUS[order.order_status] && NEXT_STATUS[order.order_status].map((s) => (
                <button key={s} className={`btn btn-sm ${s === "cancelled" ? "btn-outline" : "btn-primary"}`} onClick={() => handleStatusChange(order, s)}>
                  {LABELS[s]}
                </button>
              ))}
              {!["delivered", "cancelled"].includes(order.order_status) && (
                <>
                  <input
                    ref={(el) => (fileInputRefs.current[order.id] = el)}
                    type="file" accept="image/jpeg,image/png,image/webp" style={{ display: "none" }}
                    onChange={(e) => handleUploadProof(order, e.target.files[0])}
                  />
                  <button
                    className="btn btn-outline btn-sm" disabled={uploadingId === order.id}
                    onClick={() => fileInputRefs.current[order.id]?.click()}
                  >
                    {uploadingId === order.id ? "Uploading..." : order.has_packing_proof ? "📦 Replace Packing Photo" : "📦 Upload Packing Photo"}
                  </button>
                </>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
