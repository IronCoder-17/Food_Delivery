import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/AuthContext";
import {
  createGroupOrder, listMyGroupOrders, joinGroupOrder, getGroupOrder,
  addGroupOrderItem, removeGroupOrderItem, lockGroupOrder, checkoutGroupOrder, cancelGroupOrder,
  getRestaurantsPublic, getFoods, getAddresses,
  getGroupOrderSuggestions, suggestGroupOrderDish, voteForSuggestion, unvoteSuggestion, finalizeGroupVoting,
  splitGroupBill, getGroupBillSplit, payGroupShare,
} from "../../services/endpoints";

const STATUS_BADGE = { open: "badge-pending", locked: "badge-approved", completed: "badge-approved", cancelled: "badge-rejected" };

export default function GroupOrdersPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [restaurants, setRestaurants] = useState([]);
  const [restaurantsLoading, setRestaurantsLoading] = useState(false);
  const [restaurantsError, setRestaurantsError] = useState("");
  const [createForm, setCreateForm] = useState({ name: "", restaurant_id: "", deadline: "", enable_voting: false, max_participants: "", budget: "" });
  const [createError, setCreateError] = useState("");
  const [creating, setCreating] = useState(false);

  const [suggestions, setSuggestions] = useState([]);
  const [billSplit, setBillSplit] = useState([]);
  const [billSplitType, setBillSplitType] = useState("equal");
  const [billError, setBillError] = useState("");
  const [payingShare, setPayingShare] = useState(false);

  const [joinCode, setJoinCode] = useState("");
  const [joinError, setJoinError] = useState("");
  const [joining, setJoining] = useState(false);

  const [foods, setFoods] = useState([]);
  const [addError, setAddError] = useState("");

  const [checkoutForm, setCheckoutForm] = useState({ address: "", payment_method: "cod" });
  const [addresses, setAddresses] = useState([]);
  const [checkoutError, setCheckoutError] = useState("");
  const [checkingOut, setCheckingOut] = useState(false);

  function loadList() {
    listMyGroupOrders().then((res) => setList(res.data)).catch((err) => setError(err.message)).finally(() => setLoading(false));
  }
  useEffect(() => { loadList(); }, []);

  const loadDetail = useCallback((id) => {
    getGroupOrder(id).then((res) => {
      setDetail(res.data);
      getFoods({ restaurant_id: res.data.restaurant_id }).then((r) => setFoods(r.data)).catch(() => {});
      if (res.data.enable_voting && res.data.status === "open") {
        getGroupOrderSuggestions(id).then((r) => setSuggestions(r.data)).catch(() => {});
      }
      if (res.data.bill_split_started) {
        getGroupBillSplit(id).then((r) => setBillSplit(r.data)).catch(() => {});
      }
    }).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    loadDetail(selectedId);
    const interval = setInterval(() => loadDetail(selectedId), 5000);
    return () => clearInterval(interval);
  }, [selectedId, loadDetail]);

  function openCreate() {
    setCreateError("");
    setShowCreate(true);
    setRestaurantsLoading(true);
    setRestaurantsError("");
    getRestaurantsPublic()
      .then((res) => setRestaurants(res.data))
      .catch((err) => setRestaurantsError(err.message || "Failed to load restaurants."))
      .finally(() => setRestaurantsLoading(false));
  }

  async function handleCreate(e) {
    e.preventDefault();
    setCreateError("");
    if (!createForm.name.trim() || !createForm.restaurant_id) {
      setCreateError("Group name and restaurant are required.");
      return;
    }
    setCreating(true);
    try {
      const payload = { name: createForm.name.trim(), restaurant_id: parseInt(createForm.restaurant_id, 10) };
      if (createForm.deadline) payload.deadline = new Date(createForm.deadline).toISOString();
      if (createForm.enable_voting) payload.enable_voting = true;
      if (createForm.max_participants) payload.max_participants = parseInt(createForm.max_participants, 10);
      if (createForm.budget) payload.budget = parseFloat(createForm.budget);
      const res = await createGroupOrder(payload);
      setShowCreate(false);
      loadList();
      setSelectedId(res.data.id);
    } catch (err) {
      setCreateError(err.message || "Failed to create group order.");
    } finally {
      setCreating(false);
    }
  }

  async function handleJoin(e) {
    e.preventDefault();
    setJoinError("");
    setJoining(true);
    try {
      const res = await joinGroupOrder(joinCode.trim());
      setJoinCode("");
      loadList();
      setSelectedId(res.data.id);
    } catch (err) {
      setJoinError(err.message || "Failed to join group order.");
    } finally {
      setJoining(false);
    }
  }

  async function handleAddFood(foodId) {
    setAddError("");
    try {
      const res = await addGroupOrderItem(selectedId, foodId, 1);
      setDetail(res.data);
    } catch (err) {
      setAddError(err.message);
    }
  }

  async function handleRemoveItem(itemId) {
    try {
      const res = await removeGroupOrderItem(selectedId, itemId);
      setDetail(res.data);
    } catch (err) {
      setAddError(err.message);
    }
  }

  async function handleLock() {
    try {
      const res = await lockGroupOrder(selectedId);
      setDetail(res.data);
    } catch (err) {
      window.alert(err.message);
    }
  }

  async function handleCancel() {
    if (!confirm("Cancel this group order for everyone?")) return;
    try {
      const res = await cancelGroupOrder(selectedId);
      setDetail(res.data);
      loadList();
    } catch (err) {
      window.alert(err.message);
    }
  }

  async function handleSuggest(foodId) {
    try {
      await suggestGroupOrderDish(selectedId, foodId);
      const res = await getGroupOrderSuggestions(selectedId);
      setSuggestions(res.data);
    } catch (err) {
      window.alert(err.message);
    }
  }

  async function handleToggleVote(suggestion) {
    try {
      if (suggestion.voted_by_me) await unvoteSuggestion(selectedId, suggestion.id);
      else await voteForSuggestion(selectedId, suggestion.id);
      const res = await getGroupOrderSuggestions(selectedId);
      setSuggestions(res.data);
    } catch (err) {
      window.alert(err.message);
    }
  }

  async function handleFinalizeVoting() {
    if (!confirm("Finalize voting? The winning dish(es) will be added to the shared cart.")) return;
    try {
      const res = await finalizeGroupVoting(selectedId);
      setDetail(res.data.group_order);
      setSuggestions([]);
    } catch (err) {
      window.alert(err.message);
    }
  }

  async function handleSplitBill() {
    setBillError("");
    try {
      const res = await splitGroupBill(selectedId, billSplitType);
      setBillSplit(res.data);
      loadDetail(selectedId);
    } catch (err) {
      setBillError(err.message);
    }
  }

  async function handlePayShare() {
    setBillError("");
    setPayingShare(true);
    try {
      await payGroupShare(selectedId);
      const res = await getGroupBillSplit(selectedId);
      setBillSplit(res.data);
    } catch (err) {
      setBillError(err.message);
    } finally {
      setPayingShare(false);
    }
  }

  function openCheckout() {
    setCheckoutError("");
    getAddresses().then((res) => {
      setAddresses(res.data);
      const def = res.data.find((a) => a.is_default);
      if (def) setCheckoutForm((f) => ({ ...f, address: def.address }));
    }).catch(() => {});
  }

  async function handleCheckout(e) {
    e.preventDefault();
    setCheckoutError("");
    if (!checkoutForm.address.trim()) {
      setCheckoutError("Delivery address is required.");
      return;
    }
    setCheckingOut(true);
    try {
      const res = await checkoutGroupOrder(selectedId, checkoutForm);
      setDetail(res.data);
      loadList();
    } catch (err) {
      setCheckoutError(err.message || "Checkout failed.");
    } finally {
      setCheckingOut(false);
    }
  }

  if (selectedId && detail) {
    return (
      <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 800 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => { setSelectedId(null); setDetail(null); loadList(); }}>← All Group Orders</button>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
          <div>
            <h2 style={{ margin: 0 }}>{detail.name}</h2>
            <div style={{ fontSize: 13.5, color: "var(--gray-500)" }}>{detail.restaurant_name} · Code: <strong>{detail.invite_code}</strong></div>
          </div>
          <span className={`badge ${STATUS_BADGE[detail.status]}`}>{detail.status}</span>
        </div>

        {detail.deadline && (
          <div style={{ fontSize: 13, color: detail.is_past_deadline ? "var(--red)" : "var(--gray-500)", marginTop: 6 }}>
            Deadline: {new Date(detail.deadline).toLocaleString()}{detail.is_past_deadline ? " (passed)" : ""}
          </div>
        )}

        {detail.created_order_id && (
          <div className="alert alert-success" style={{ marginTop: 12 }}>
            Order placed! <button className="btn btn-ghost btn-sm" onClick={() => navigate("/orders")}>View Orders</button>
          </div>
        )}

        <div className="card" style={{ padding: 16, marginTop: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <strong>Members ({detail.members.length}{detail.max_participants ? ` / ${detail.max_participants}` : ""})</strong>
            <strong style={{ color: detail.over_budget ? "var(--red)" : "inherit" }}>Group Total: ₹{detail.group_total}</strong>
          </div>
          <div style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 4 }}>
            {detail.members.map((m) => `${m.name}${m.is_host ? " (Host)" : ""}`).join(", ")}
          </div>
          {detail.budget != null && (
            <div style={{ fontSize: 13, marginTop: 6, color: detail.over_budget ? "var(--red)" : "var(--gray-500)" }}>
              Budget: ₹{detail.budget} {detail.over_budget && "— over budget!"}
            </div>
          )}
        </div>

        {addError && <div className="alert alert-error">{addError}</div>}

        {detail.enable_voting && detail.status === "open" && (
          <div className="card" style={{ padding: 16, marginTop: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong>🗳️ Vote for Dishes</strong>
              {detail.is_host && (
                <button className="btn btn-primary btn-sm" onClick={handleFinalizeVoting}>Finalize Voting</button>
              )}
            </div>
            {suggestions.length === 0 ? (
              <p style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 8 }}>
                No dishes suggested yet. Suggest one from the menu below.
              </p>
            ) : (
              <div style={{ marginTop: 10 }}>
                {suggestions.map((s) => (
                  <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderTop: "1px solid var(--gray-100)" }}>
                    <div>
                      <div style={{ fontSize: 14 }}>{s.food_name}</div>
                      <div style={{ fontSize: 12, color: "var(--gray-500)" }}>Suggested by {s.suggested_by_name}</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontWeight: 700 }}>{s.vote_count} vote{s.vote_count !== 1 ? "s" : ""}</span>
                      <button className={`btn btn-sm ${s.voted_by_me ? "btn-primary" : "btn-outline"}`} onClick={() => handleToggleVote(s)}>
                        {s.voted_by_me ? "Voted ✓" : "Vote"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {foods.length > 0 && (
              <details style={{ marginTop: 10 }}>
                <summary style={{ cursor: "pointer", fontSize: 13.5, color: "var(--orange)" }}>+ Suggest a dish from the menu</summary>
                <div style={{ maxHeight: 160, overflowY: "auto", marginTop: 8 }}>
                  {foods.map((f) => (
                    <div key={f.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "5px 0" }}>
                      <span style={{ fontSize: 13.5 }}>{f.name} — ₹{f.effective_price}</span>
                      <button className="btn btn-ghost btn-sm" disabled={!f.is_available} onClick={() => handleSuggest(f.id)}>Suggest</button>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        )}

        {detail.status === "open" && !detail.enable_voting && foods.length > 0 && (
          <div className="card" style={{ padding: 16, marginTop: 16 }}>
            <strong>Add Items</strong>
            <div style={{ maxHeight: 200, overflowY: "auto", marginTop: 8 }}>
              {foods.map((f) => (
                <div key={f.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "5px 0" }}>
                  <span style={{ fontSize: 14 }}>{f.name} — ₹{f.effective_price}</span>
                  <button className="btn btn-outline btn-sm" disabled={!f.is_available} onClick={() => handleAddFood(f.id)}>
                    {f.is_available ? "+ Add" : "Sold Out"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: 16 }}>
          {detail.contributions.map((c) => (
            <div key={c.customer_id} className="card" style={{ padding: 14, marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600 }}>
                <span>{c.customer_name}</span><span>₹{c.subtotal}</span>
              </div>
              {c.items.map((i) => (
                <div key={i.id} style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5, padding: "3px 0" }}>
                  <span>{i.food_name} × {i.quantity}{!i.is_available ? " (unavailable)" : ""}</span>
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    ₹{i.line_total}
                    {i.can_remove && detail.status === "open" && (
                      <button className="btn btn-ghost btn-sm" style={{ color: "var(--red)" }} onClick={() => handleRemoveItem(i.id)}>Remove</button>
                    )}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>

        {detail.is_host && detail.status === "open" && (
          <button className="btn btn-primary" onClick={handleLock}>🔒 Lock Order</button>
        )}
        {detail.is_host && (detail.status === "open" || detail.status === "locked") && (
          <button className="btn btn-ghost" style={{ marginLeft: 8, color: "var(--red)" }} onClick={handleCancel}>Cancel Group Order</button>
        )}

        {detail.is_host && (detail.status === "open" || detail.status === "locked") && (
          <form onSubmit={handleCheckout} className="card" style={{ padding: 16, marginTop: 16 }} onFocus={openCheckout}>
            <strong>Checkout ({detail.status === "open" ? "will lock automatically" : "locked"})</strong>
            {checkoutError && <div className="alert alert-error">{checkoutError}</div>}
            {addresses.length > 0 && (
              <div style={{ display: "flex", gap: 8, margin: "8px 0", flexWrap: "wrap" }}>
                {addresses.map((a) => (
                  <button type="button" key={a.id} className="btn btn-outline btn-sm" onClick={() => setCheckoutForm((f) => ({ ...f, address: a.address }))}>{a.label}</button>
                ))}
              </div>
            )}
            <div className="field">
              <label>Delivery Address</label>
              <textarea className="input" rows={2} value={checkoutForm.address} onChange={(e) => setCheckoutForm({ ...checkoutForm, address: e.target.value })} />
            </div>
            <div className="field">
              <label>Payment Method (host pays)</label>
              <select className="input" value={checkoutForm.payment_method} onChange={(e) => setCheckoutForm({ ...checkoutForm, payment_method: e.target.value })}>
                <option value="cod">Cash on Delivery</option>
                <option value="wallet">Wallet</option>
              </select>
            </div>
            <button className="btn btn-primary" disabled={checkingOut}>{checkingOut ? "Placing..." : "Place Group Order"}</button>
          </form>
        )}

        {detail.status === "completed" && (
          <div className="card" style={{ padding: 16, marginTop: 16 }}>
            <strong>💳 Split the Bill</strong>
            {billError && <div className="alert alert-error">{billError}</div>}

            {!detail.bill_split_started ? (
              detail.is_host ? (
                <div style={{ display: "flex", gap: 10, alignItems: "flex-end", marginTop: 10, flexWrap: "wrap" }}>
                  <div className="field" style={{ margin: 0 }}>
                    <label>Split Method</label>
                    <select className="input" value={billSplitType} onChange={(e) => setBillSplitType(e.target.value)}>
                      <option value="equal">Equal Split</option>
                      <option value="item_based">By What Each Person Ordered</option>
                    </select>
                  </div>
                  <button className="btn btn-primary" onClick={handleSplitBill}>Split Bill</button>
                </div>
              ) : (
                <p style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 8 }}>
                  Waiting for the host to split the bill.
                </p>
              )
            ) : (
              <div style={{ marginTop: 10 }}>
                {billSplit.map((row) => (
                  <div key={row.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderTop: "1px solid var(--gray-100)" }}>
                    <span style={{ fontSize: 14 }}>{row.customer_name}</span>
                    <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      ₹{row.amount}
                      <span className={`badge ${row.status === "paid" ? "badge-approved" : row.status === "failed" ? "badge-rejected" : "badge-pending"}`}>
                        {row.status}
                      </span>
                    </span>
                  </div>
                ))}
                {billSplit.some((r) => ["pending", "failed"].includes(r.status) && r.customer_id === user?.customer_id) && (
                  <button className="btn btn-primary btn-sm" style={{ marginTop: 12 }} disabled={payingShare} onClick={handlePayShare}>
                    {payingShare ? "Paying..." : "Pay My Share (from Wallet)"}
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 720 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>👥 Group Orders</h2>
        {!showCreate && <button className="btn btn-primary btn-sm" onClick={openCreate}>+ New Group Order</button>}
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleJoin} className="card" style={{ padding: 16, marginTop: 16, display: "flex", gap: 8, alignItems: "flex-end" }}>
        <div className="field" style={{ flex: 1, margin: 0 }}>
          <label>Have an invite code?</label>
          <input className="input" placeholder="QB-XXXXXX" value={joinCode} onChange={(e) => setJoinCode(e.target.value)} />
        </div>
        <button className="btn btn-outline" disabled={joining || !joinCode.trim()}>{joining ? "Joining..." : "Join"}</button>
      </form>
      {joinError && <div className="alert alert-error">{joinError}</div>}

      {showCreate && (
        <form onSubmit={handleCreate} className="card" style={{ padding: 20, marginTop: 16 }}>
          <h4 style={{ marginTop: 0 }}>New Group Order</h4>
          {createError && <div className="alert alert-error">{createError}</div>}
          <div className="field">
            <label>Group Name</label>
            <input className="input" value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} placeholder="e.g. Office Lunch" />
          </div>
          <div className="field">
            <label>Restaurant</label>
            {restaurantsError && <div className="alert alert-error">{restaurantsError}</div>}
            <select className="input" value={createForm.restaurant_id} disabled={restaurantsLoading}
              onChange={(e) => setCreateForm({ ...createForm, restaurant_id: e.target.value })}>
              <option value="">{restaurantsLoading ? "Loading restaurants..." : "Select a restaurant"}</option>
              {restaurants.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
            {!restaurantsLoading && !restaurantsError && restaurants.length === 0 && (
              <div className="hint" style={{ color: "var(--red)" }}>
                No approved restaurants are available yet. A restaurant must be approved by an admin (Admin → Restaurants) before it can be selected here.
              </div>
            )}
          </div>
          <div className="field">
            <label>Order Deadline (optional)</label>
            <input className="input" type="datetime-local" value={createForm.deadline} onChange={(e) => setCreateForm({ ...createForm, deadline: e.target.value })} />
          </div>
          <div className="grid grid-2">
            <div className="field">
              <label>Max Participants (optional)</label>
              <input className="input" type="number" min="1" value={createForm.max_participants}
                onChange={(e) => setCreateForm({ ...createForm, max_participants: e.target.value })} />
            </div>
            <div className="field">
              <label>Budget (optional, ₹)</label>
              <input className="input" type="number" min="1" value={createForm.budget}
                onChange={(e) => setCreateForm({ ...createForm, budget: e.target.value })} />
            </div>
          </div>
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14, marginBottom: 14 }}>
            <input type="checkbox" checked={createForm.enable_voting} onChange={(e) => setCreateForm({ ...createForm, enable_voting: e.target.checked })} />
            Enable dish voting (members suggest & vote instead of adding directly)
          </label>
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-primary" disabled={creating}>{creating ? "Creating..." : "Create & Get Invite Code"}</button>
            <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
          </div>
        </form>
      )}

      <div style={{ marginTop: 20 }}>
        {loading ? (
          <div className="skeleton" style={{ height: 150 }} />
        ) : list.length === 0 ? (
          <div className="empty-state"><h3>No group orders yet</h3><p>Start one and invite friends, or join with a code.</p></div>
        ) : (
          list.map((go) => (
            <div key={go.id} className="card" style={{ padding: 16, marginBottom: 12, cursor: "pointer" }} onClick={() => setSelectedId(go.id)}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{go.name}</strong>
                <span className={`badge ${STATUS_BADGE[go.status]}`}>{go.status}</span>
              </div>
              <div style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 4 }}>
                {go.restaurant_name} · {go.members.length} member{go.members.length !== 1 ? "s" : ""} · ₹{go.group_total}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}