import { useEffect, useState, useCallback } from "react";
import {
  getCategories, getFoods, addToCart as addToCartApi,
  getFavoriteStatus, addFavoriteFood, removeFavoriteFood,
  getPublicCombos, addComboToCart, getSponsoredRestaurants,
  getMoods, getAllergens,
} from "../../services/endpoints";
import { useAuth } from "../../hooks/AuthContext";
import { useCart } from "../../hooks/CartContext";
import { useAuthority } from "../../hooks/AuthorityContext";
import FoodCard from "../../components/FoodCard";

export default function CustomerDashboard() {
  const { user } = useAuth();
  const { refreshCart } = useCart();
  const { can } = useAuthority();
  const [categories, setCategories] = useState([]);
  const [foods, setFoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [favoriteFoodIds, setFavoriteFoodIds] = useState(new Set());
  const [combos, setCombos] = useState([]);
  const [sponsored, setSponsored] = useState([]);

  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [veg, setVeg] = useState("");
  const [sort, setSort] = useState("");
  const [moods, setMoods] = useState([]);
  const [moodId, setMoodId] = useState("");
  const [allergens, setAllergens] = useState([]);
  const [allergenId, setAllergenId] = useState("");
  const [allergenDisclaimer, setAllergenDisclaimer] = useState("");

  useEffect(() => {
    getCategories().then((res) => setCategories(res.data)).catch(() => {});
    getPublicCombos().then((res) => setCombos(res.data)).catch(() => {});
    getSponsoredRestaurants("homepage").then((res) => setSponsored(res.data)).catch(() => {});
    getMoods().then((res) => setMoods(res.data)).catch(() => {});
    getAllergens().then((res) => { setAllergens(res.data.allergens); setAllergenDisclaimer(res.data.disclaimer); }).catch(() => {});
  }, []);

  const loadFoods = useCallback(() => {
    setLoading(true);
    setError("");
    const params = { include_unavailable: "true" };
    if (search) params.search = search;
    if (categoryId) params.category_id = categoryId;
    if (veg) params.veg = veg;
    if (sort) params.sort = sort;
    if (moodId) params.mood_id = moodId;
    if (allergenId) params.allergen_id = allergenId;
    getFoods(params)
      .then((res) => setFoods(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [search, categoryId, veg, sort, moodId, allergenId]);

  useEffect(() => { loadFoods(); }, [loadFoods]);

  // Once foods are loaded, bulk-check which of them are already favorited
  // (single request instead of one per card) -- skipped entirely if the
  // admin has disabled Favorites for this customer.
  useEffect(() => {
    if (!can("customer.favorites") || foods.length === 0) return;
    let cancelled = false;
    getFavoriteStatus(foods.map((f) => f.id))
      .then((res) => { if (!cancelled) setFavoriteFoodIds(new Set(res.data.foods)); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [foods, can]);

  async function handleToggleFavorite(food) {
    const isFav = favoriteFoodIds.has(food.id);
    // optimistic update, reverted on failure
    setFavoriteFoodIds((prev) => {
      const next = new Set(prev);
      if (isFav) next.delete(food.id); else next.add(food.id);
      return next;
    });
    try {
      if (isFav) await removeFavoriteFood(food.id);
      else await addFavoriteFood(food.id);
    } catch (err) {
      setFavoriteFoodIds((prev) => {
        const next = new Set(prev);
        if (isFav) next.add(food.id); else next.delete(food.id);
        return next;
      });
      setToast(err.message);
      setTimeout(() => setToast(""), 2500);
    }
  }

  async function handleAdd(food) {
    try {
      await addToCartApi(food.id, 1);
      await refreshCart();
      setToast(`${food.name} added to cart`);
      setTimeout(() => setToast(""), 1800);
    } catch (err) {
      setToast(err.message);
      setTimeout(() => setToast(""), 2500);
    }
  }

  async function handleAddCombo(combo) {
    try {
      await addComboToCart(combo.id, 1);
      await refreshCart();
      setToast(`${combo.name} added to cart`);
      setTimeout(() => setToast(""), 1800);
    } catch (err) {
      setToast(err.message);
      setTimeout(() => setToast(""), 2500);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <div style={{ background: "linear-gradient(135deg, var(--orange), var(--orange-dark))", borderRadius: 14, padding: "30px 28px", color: "#fff", marginBottom: 24 }}>
        <h1 style={{ color: "#fff", margin: 0 }}>Hi {user?.name?.split(" ")[0]}, what are you craving today?</h1>
        <p style={{ opacity: 0.9, marginTop: 6 }}>Browse dishes from top-rated restaurants near you.</p>
      </div>

      {toast && <div className="alert alert-success">{toast}</div>}

      {sponsored.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ marginBottom: 10 }}>Featured Restaurants</h3>
          <div className="grid grid-4">
            {sponsored.map((s) => (
              <div key={s.restaurant_id} className="card" style={{ overflow: "hidden", position: "relative" }}>
                <span style={{
                  position: "absolute", top: 8, left: 8, background: "rgba(0,0,0,0.65)", color: "#fff",
                  fontSize: 10.5, fontWeight: 700, padding: "2px 7px", borderRadius: 5, zIndex: 1,
                }}>
                  Sponsored
                </span>
                <div style={{ height: 100, background: "var(--orange-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 30 }}>
                  {s.cover_image_url ? <img src={s.cover_image_url} alt={s.restaurant_name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "🍽️"}
                </div>
                <div style={{ padding: 12 }}>
                  <div style={{ fontWeight: 600 }}>{s.restaurant_name}</div>
                  {s.rating > 0 && <div style={{ fontSize: 12.5, color: "var(--gray-500)" }}>⭐ {s.rating}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {combos.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ marginBottom: 10 }}>🎁 Combos & Deals</h3>
          <div className="grid grid-4">
            {combos.map((c) => (
              <div key={c.id} className="card" style={{ overflow: "hidden", display: "flex", flexDirection: "column", position: "relative" }}>
                <div style={{ height: 110, background: "var(--orange-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 34, position: "relative" }}>
                  {c.image_url ? <img src={c.image_url} alt={c.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "🎁"}
                  {c.flash_sale && (
                    <span style={{ position: "absolute", top: 8, left: 8, background: "#e63946", color: "#fff", fontSize: 11, fontWeight: 700, padding: "3px 8px", borderRadius: 6 }}>
                      🔥 -{c.flash_sale.discount_percent}%
                    </span>
                  )}
                </div>
                <div style={{ padding: 14, flex: 1, display: "flex", flexDirection: "column" }}>
                  <h4 style={{ margin: "0 0 2px" }}>{c.name}</h4>
                  <div style={{ fontSize: 13, color: "var(--gray-500)", marginBottom: 6 }}>{c.restaurant_name}</div>
                  <p style={{ fontSize: 13, color: "var(--gray-700)", flex: 1 }}>
                    {c.items.map((i) => `${i.food_name} ×${i.quantity}`).join(", ")}
                  </p>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 8 }}>
                    <div>
                      <span style={{ fontWeight: 700, fontSize: 16 }}>₹{c.effective_price}</span>
                      <span style={{ marginLeft: 6, fontSize: 12.5, color: "var(--gray-500)", textDecoration: "line-through" }}>₹{c.original_price}</span>
                    </div>
                    <button className="btn btn-primary btn-sm" onClick={() => handleAddCombo(c)}>Add +</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ padding: 16, marginBottom: 22, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <input className="input" style={{ flex: "2 1 220px" }} placeholder="Search food..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className="input" style={{ flex: "1 1 160px" }} value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
          <option value="">All Categories</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select className="input" style={{ flex: "1 1 140px" }} value={veg} onChange={(e) => setVeg(e.target.value)}>
          <option value="">Veg & Non-Veg</option>
          <option value="true">Veg Only</option>
          <option value="false">Non-Veg Only</option>
        </select>
        <select className="input" style={{ flex: "1 1 160px" }} value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="">Sort: Newest</option>
          <option value="price_low">Price: Low to High</option>
          <option value="price_high">Price: High to Low</option>
          <option value="rating">Rating</option>
        </select>
        {allergens.length > 0 && (
          <select className="input" style={{ flex: "1 1 180px" }} value={allergenId} onChange={(e) => setAllergenId(e.target.value)}
            title={allergenDisclaimer}>
            <option value="">Any Ingredients</option>
            {allergens.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        )}
      </div>

      {moods.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <div style={{ fontSize: 13.5, fontWeight: 700, color: "var(--gray-700)", marginBottom: 8 }}>What are you feeling?</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {moods.map((m) => (
              <button key={m.id} className="btn btn-sm" onClick={() => setMoodId(moodId === String(m.id) ? "" : String(m.id))}
                style={{
                  background: moodId === String(m.id) ? "var(--orange)" : "var(--white)",
                  color: moodId === String(m.id) ? "#fff" : "var(--ink)", border: "1px solid var(--gray-300)",
                }}>
                {m.emoji} {m.name}
              </button>
            ))}
            {moodId && <button className="btn btn-sm btn-ghost" onClick={() => setMoodId("")}>Clear Mood</button>}
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 22 }}>
        {categories.map((c) => (
          <button key={c.id} className="btn btn-sm" onClick={() => setCategoryId(String(c.id))}
            style={{ background: categoryId === String(c.id) ? "var(--orange)" : "var(--white)", color: categoryId === String(c.id) ? "#fff" : "var(--ink)", border: "1px solid var(--gray-300)" }}>
            {c.name}
          </button>
        ))}
        {categoryId && <button className="btn btn-sm btn-ghost" onClick={() => setCategoryId("")}>Clear</button>}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="grid grid-4">
          {Array.from({ length: 8 }).map((_, i) => <div key={i} className="skeleton" style={{ height: 260 }} />)}
        </div>
      ) : foods.length === 0 ? (
        <div className="empty-state">
          <div style={{ fontSize: 40 }}>🍽️</div>
          <h3>No dishes found</h3>
          <p>Try adjusting your search or filters.</p>
        </div>
      ) : (
        <div className="grid grid-4">
          {foods.map((f) => (
            <FoodCard
              key={f.id}
              food={f}
              onAdd={handleAdd}
              isFavorite={favoriteFoodIds.has(f.id)}
              onToggleFavorite={can("customer.favorites") ? handleToggleFavorite : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
}
