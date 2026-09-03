import { useEffect, useState } from "react";
import {
  getFavoriteFoods, removeFavoriteFood, getFavoriteRestaurants, removeFavoriteRestaurant,
  addToCart as addToCartApi,
} from "../../services/endpoints";
import { useCart } from "../../hooks/CartContext";
import FoodCard from "../../components/FoodCard";

export default function FavoritesPage() {
  const { refreshCart } = useCart();
  const [tab, setTab] = useState("foods");
  const [foods, setFoods] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  function load() {
    setLoading(true);
    setError("");
    Promise.all([getFavoriteFoods(), getFavoriteRestaurants()])
      .then(([foodsRes, restaurantsRes]) => {
        setFoods(foodsRes.data);
        setRestaurants(restaurantsRes.data);
      })
      .catch((err) => setError(err.message || "Failed to load favorites."))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  async function handleRemoveFood(food) {
    setFoods((prev) => prev.filter((f) => f.id !== food.id));
    try {
      await removeFavoriteFood(food.id);
    } catch (err) {
      setError(err.message);
      load();
    }
  }

  async function handleRemoveRestaurant(r) {
    setRestaurants((prev) => prev.filter((x) => x.id !== r.id));
    try {
      await removeFavoriteRestaurant(r.id);
    } catch (err) {
      setError(err.message);
      load();
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

  if (loading) {
    return (
      <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
        <h2>❤️ Favorites</h2>
        <div className="grid grid-4">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton" style={{ height: 220 }} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60 }}>
      <h2>❤️ Favorites</h2>
      {error && <div className="alert alert-error">{error}</div>}
      {toast && <div className="alert alert-success">{toast}</div>}

      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        <button className={`btn btn-sm ${tab === "foods" ? "btn-primary" : "btn-outline"}`} onClick={() => setTab("foods")}>
          Foods ({foods.length})
        </button>
        <button className={`btn btn-sm ${tab === "restaurants" ? "btn-primary" : "btn-outline"}`} onClick={() => setTab("restaurants")}>
          Restaurants ({restaurants.length})
        </button>
      </div>

      {tab === "foods" && (
        foods.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: 40 }}>🤍</div>
            <h3>No favorite foods yet</h3>
            <p>Tap the heart on any dish to save it here.</p>
          </div>
        ) : (
          <div className="grid grid-4">
            {foods.map((f) => (
              <FoodCard key={f.id} food={f} onAdd={handleAdd} isFavorite onToggleFavorite={handleRemoveFood} />
            ))}
          </div>
        )
      )}

      {tab === "restaurants" && (
        restaurants.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: 40 }}>🤍</div>
            <h3>No favorite restaurants yet</h3>
            <p>Favorite restaurants you love for quick access.</p>
          </div>
        ) : (
          <div className="grid grid-4">
            {restaurants.map((r) => (
              <div key={r.id} className="card" style={{ overflow: "hidden", display: "flex", flexDirection: "column" }}>
                <div style={{ height: 120, background: "var(--orange-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36 }}>
                  {r.cover_image_url ? <img src={r.cover_image_url} alt={r.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "🍽️"}
                </div>
                <div style={{ padding: 14, flex: 1, display: "flex", flexDirection: "column" }}>
                  <h4 style={{ margin: "0 0 4px" }}>{r.name}</h4>
                  {r.rating > 0 && <div style={{ fontSize: 13, color: "var(--gray-500)", marginBottom: 8 }}>⭐ {r.rating}</div>}
                  <p style={{ fontSize: 13.5, color: "var(--gray-700)", flex: 1 }}>{r.description?.slice(0, 80)}</p>
                  <button className="btn btn-outline btn-sm" onClick={() => handleRemoveRestaurant(r)}>💔 Remove</button>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  );
}
