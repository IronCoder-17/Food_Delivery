import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/AuthContext";
import { useCart } from "../../hooks/CartContext";
import { createOrder, createRazorpayOrder, verifyRazorpayPayment, getWallet, getAddresses, getTipSuggestions } from "../../services/endpoints";
import { useAuthority } from "../../hooks/AuthorityContext";

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

export default function CheckoutPage() {
  const { user } = useAuth();
  const { cart, refreshCart } = useCart();
  const { can } = useAuthority();
  const navigate = useNavigate();

  const [address, setAddress] = useState("");
  const [method, setMethod] = useState("cod");
  const [walletBalance, setWalletBalance] = useState(null);
  const [error, setError] = useState("");
  const [placing, setPlacing] = useState(false);

  const [savedAddresses, setSavedAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null); // null = "typed manually"

  const [tipSuggestions, setTipSuggestions] = useState([]);
  const [tipAmount, setTipAmount] = useState(0);
  const [customTip, setCustomTip] = useState("");
  const [ecoDelivery, setEcoDelivery] = useState(false);
  const [roundUpDonation, setRoundUpDonation] = useState(false);

  useEffect(() => {
    if (!cart.subtotal) return;
    getTipSuggestions(cart.subtotal).then((res) => setTipSuggestions(res.data.suggestions)).catch(() => {});
  }, [cart.subtotal]);

  const donationPreview = roundUpDonation
    ? (() => {
        const preTotal = Number(cart.total) + Number(tipAmount || 0);
        const roundedUp = Math.ceil(preTotal);
        return roundedUp - preTotal <= 0 ? 1 : Math.round((roundedUp - preTotal) * 100) / 100;
      })()
    : 0;
  const estimatedTotal = Math.round((Number(cart.total) + Number(tipAmount || 0) + donationPreview) * 100) / 100;

  useEffect(() => { refreshCart(); }, [refreshCart]);
  useEffect(() => { getWallet().then((res) => setWalletBalance(res.data.balance)).catch(() => {}); }, []);

  // Load saved addresses (if the admin hasn't restricted the feature) and
  // pre-fill the delivery address with the customer's default one, without
  // removing the ability to type a one-off address instead.
  useEffect(() => {
    if (!can("customer.manage_addresses")) return;
    getAddresses()
      .then((res) => {
        setSavedAddresses(res.data);
        const def = res.data.find((a) => a.is_default) || res.data[0];
        if (def) {
          setSelectedAddressId(def.id);
          setAddress(def.address);
        }
      })
      .catch(() => {});
  }, [can]);

  function selectSavedAddress(addr) {
    setSelectedAddressId(addr.id);
    setAddress(addr.address);
  }

  function switchToManualEntry() {
    setSelectedAddressId(null);
    setAddress("");
  }

  const insufficientWallet = method === "wallet" && walletBalance !== null && walletBalance < estimatedTotal;

  async function handlePlaceOrder() {
    setError("");
    if (!address.trim()) {
      setError("Please enter a delivery address.");
      return;
    }
    setPlacing(true);
    try {
      const orderRes = await createOrder({
        payment_method: method, address,
        ...(selectedAddressId ? { address_id: selectedAddressId } : {}),
        tip_amount: Number(tipAmount) || 0,
        eco_delivery: ecoDelivery,
        round_up_donation: roundUpDonation,
      });
      const order = orderRes.data;

      if (method === "razorpay") {
        const ok = await loadRazorpayScript();
        if (!ok) {
          setError("Could not load Razorpay checkout. Check your internet connection.");
          setPlacing(false);
          return;
        }
        let rpOrder;
        try {
          const rpRes = await createRazorpayOrder(order.id);
          rpOrder = rpRes.data;
        } catch (err) {
          setError(err.message); // e.g. "Razorpay is not configured on this server..."
          setPlacing(false);
          return;
        }

        const rzp = new window.Razorpay({
          key: rpOrder.key_id,
          amount: rpOrder.amount,
          currency: rpOrder.currency,
          name: "QuickBite",
          description: `Order #${order.id}`,
          order_id: rpOrder.razorpay_order_id,
          handler: async function (response) {
            try {
              await verifyRazorpayPayment({
                order_id: order.id,
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              });
              await refreshCart();
              navigate(`/orders`);
            } catch (err) {
              setError(err.message);
            }
          },
          modal: { ondismiss: () => setPlacing(false) },
          theme: { color: "#E4602A" },
        });
        rzp.open();
        return; // don't navigate yet; wait for handler
      }

      await refreshCart();
      navigate("/orders");
    } catch (err) {
      setError(err.message);
    } finally {
      if (method !== "razorpay") setPlacing(false);
    }
  }

  if (cart.items.length === 0) {
    return (
      <div className="container" style={{ paddingTop: 60 }}>
        <div className="empty-state"><h3>Your cart is empty</h3></div>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 700 }}>
      <h2>Checkout</h2>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card" style={{ padding: 20, marginBottom: 18 }}>
        <h4>Customer Details</h4>
        <div style={{ fontSize: 14.5, color: "var(--gray-700)", lineHeight: 1.8 }}>
          <div><strong>Name:</strong> {user?.name}</div>
          <div><strong>Email:</strong> {user?.email}</div>
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>Delivery Address</label>

          {savedAddresses.length > 0 && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
              {savedAddresses.map((a) => (
                <button
                  type="button" key={a.id}
                  className={`btn btn-sm ${selectedAddressId === a.id ? "btn-primary" : "btn-outline"}`}
                  onClick={() => selectSavedAddress(a)}
                  title={a.address}
                >
                  {a.label === "Home" ? "🏠" : a.label === "Work" ? "🏢" : a.label === "Hostel" ? "🏫" : "📍"} {a.label}
                  {a.is_default ? " (Default)" : ""}
                </button>
              ))}
              <button
                type="button"
                className={`btn btn-sm ${selectedAddressId === null ? "btn-primary" : "btn-outline"}`}
                onClick={switchToManualEntry}
              >
                ✎ Type a different address
              </button>
            </div>
          )}

          <textarea
            className="input" rows={2} value={address}
            onChange={(e) => { setAddress(e.target.value); setSelectedAddressId(null); }}
            placeholder="Enter your full delivery address"
          />
          {can("customer.manage_addresses") && savedAddresses.length === 0 && (
            <div className="hint">
              Tip: save this address for next time from the <a href="/addresses">Addresses</a> page.
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 18 }}>
        <h4>Order Summary</h4>
        {cart.items.map((i) => (
          <div key={i.id} style={{ display: "flex", justifyContent: "space-between", fontSize: 14.5, padding: "4px 0" }}>
            <span>{i.food_name} × {i.quantity}</span><span>₹{i.line_total}</span>
          </div>
        ))}
        <div style={{ borderTop: "1px solid var(--gray-100)", marginTop: 8, paddingTop: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}><span>Subtotal</span><span>₹{cart.subtotal}</span></div>
          <div style={{ display: "flex", justifyContent: "space-between" }}><span>Delivery Fee</span><span>₹{cart.delivery_fee}</span></div>
          {Number(tipAmount) > 0 && <div style={{ display: "flex", justifyContent: "space-between" }}><span>Tip</span><span>₹{tipAmount}</span></div>}
          {roundUpDonation && <div style={{ display: "flex", justifyContent: "space-between" }}><span>Donation</span><span>₹{donationPreview}</span></div>}
          <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700, fontSize: 17 }}><span>Total</span><span style={{ color: "var(--orange)" }}>₹{estimatedTotal}</span></div>
        </div>
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 18 }}>
        <h4>🛵 Delivery Extras</h4>
        <div className="field">
          <label>Add a Tip for Your Delivery Partner (optional)</label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" className={`btn btn-sm ${Number(tipAmount) === 0 ? "btn-primary" : "btn-outline"}`}
              onClick={() => { setTipAmount(0); setCustomTip(""); }}>No Tip</button>
            {tipSuggestions.map((t, idx) => (
              <button type="button" key={idx}
                className={`btn btn-sm ${Number(tipAmount) === t.amount && !customTip ? "btn-primary" : "btn-outline"}`}
                onClick={() => { setTipAmount(t.amount); setCustomTip(""); }}
                title={t.reason}
              >
                ₹{t.amount}
              </button>
            ))}
            <input
              className="input" style={{ width: 100 }} type="number" min="0" placeholder="Custom ₹"
              value={customTip}
              onChange={(e) => { setCustomTip(e.target.value); setTipAmount(parseFloat(e.target.value) || 0); }}
            />
          </div>
          <p style={{ fontSize: 12, color: "var(--gray-500)", marginTop: 4 }}>Tipping is always optional.</p>
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14, marginTop: 10 }}>
          <input type="checkbox" checked={ecoDelivery} onChange={(e) => setEcoDelivery(e.target.checked)} />
          🌱 Eco Delivery (bike delivery / reduced packaging, where available)
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14, marginTop: 10 }}>
          <input type="checkbox" checked={roundUpDonation} onChange={(e) => setRoundUpDonation(e.target.checked)} />
          ❤️ Round up my bill to donate {roundUpDonation && `(₹${donationPreview} donation)`}
        </label>
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 18 }}>
        <h4>Payment Method</h4>
        {[
          { id: "razorpay", label: "💳 Razorpay (Card / UPI / Netbanking)" },
          { id: "cod", label: "💵 Cash on Delivery" },
          { id: "wallet", label: `👛 Wallet ${walletBalance !== null ? `(Balance: ₹${walletBalance})` : ""}` },
        ].map((opt) => (
          <label key={opt.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 4px", cursor: "pointer" }}>
            <input type="radio" name="payment" checked={method === opt.id} onChange={() => setMethod(opt.id)} />
            {opt.label}
          </label>
        ))}
        {insufficientWallet && <div className="alert alert-error" style={{ marginTop: 8 }}>Insufficient wallet balance for this order.</div>}
      </div>

      <button className="btn btn-primary btn-block" disabled={placing || insufficientWallet} onClick={handlePlaceOrder}>
        {placing ? <span className="spinner" /> : `Place Order · ₹${estimatedTotal}`}
      </button>
    </div>
  );
}
