import { useState } from "react";
import { matchRecipeFromUrl, matchRecipeFromIngredients, addToCart as addToCartApi } from "../../services/endpoints";
import { useCart } from "../../hooks/CartContext";

export default function RecipeToOrderPage() {
  const [url, setUrl] = useState("");
  const [manualInput, setManualInput] = useState("");
  const [showUrl, setShowUrl] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [ingredients, setIngredients] = useState([]);
  const [matches, setMatches] = useState([]);
  const [addingId, setAddingId] = useState(null);
  const [toast, setToast] = useState("");
  const { refreshCart } = useCart();

  async function handleUrlSubmit(e) {
    e.preventDefault();
    setError(""); setInfo(""); setMatches([]); setIngredients([]);
    if (!url.trim()) return;
    setLoading(true);
    try {
      const res = await matchRecipeFromUrl(url.trim());
      if (res.data.needs_manual_input) {
        setInfo(res.data.error || "Couldn't process that URL automatically.");
      } else {
        setIngredients(res.data.ingredients);
        setMatches(res.data.matches);
        if (res.data.matches.length === 0) {
          setInfo("Found ingredients, but no matching dishes on the menu right now.");
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleManualSubmit(e) {
    e.preventDefault();
    setError(""); setInfo("");
    const list = manualInput.split(",").map((s) => s.trim()).filter(Boolean);
    if (list.length === 0) {
      setError("Enter at least one ingredient, separated by commas.");
      return;
    }
    setLoading(true);
    try {
      const res = await matchRecipeFromIngredients(list);
      setIngredients(res.data.ingredients);
      setMatches(res.data.matches);
      if (res.data.matches.length === 0) {
        setInfo("No matching dishes found for those ingredients right now.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(match) {
    if (addingId) return;
    setAddingId(match.food_id);
    try {
      await addToCartApi(match.food_id, 1);
      await refreshCart();
      setToast(`Added "${match.food_name}" to your cart!`);
      setTimeout(() => setToast(""), 2500);
    } catch (err) {
      setError(err.message);
    } finally {
      setAddingId(null);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 700 }}>
      <h2 style={{ marginTop: 0 }}>🍳 Recipe-to-Order</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Paste a recipe link, or enter ingredients yourself, and we'll find matching dishes on the menu.
      </p>

      <form onSubmit={handleManualSubmit} className="card" style={{ padding: 18, marginBottom: 14 }}>
        <div className="field">
          <label>Ingredients (comma-separated)</label>
          <input className="input" value={manualInput} onChange={(e) => setManualInput(e.target.value)} placeholder="paneer, tomato, onion, capsicum, cheese" />
        </div>
        <button className="btn btn-primary" disabled={loading}>{loading ? "Matching..." : "Find Matching Dishes"}</button>
      </form>

      <button className="btn btn-ghost btn-sm" onClick={() => setShowUrl((v) => !v)} style={{ marginBottom: 10 }}>
        {showUrl ? "Hide" : "Or paste a recipe URL"}
      </button>

      {showUrl && (
        <form onSubmit={handleUrlSubmit} className="card" style={{ padding: 18, marginBottom: 14 }}>
          <div className="field">
            <label>Recipe URL</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input className="input" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/recipe" />
              <button className="btn btn-primary" disabled={loading}>{loading ? "Working..." : "Match"}</button>
            </div>
          </div>
        </form>
      )}

      {toast && <div className="alert alert-success">{toast}</div>}
      {error && <div className="alert alert-error">{error}</div>}
      {info && <div className="alert alert-info">{info}</div>}

      {ingredients.length > 0 && (
        <p style={{ fontSize: 13, color: "var(--gray-500)" }}>
          Matching against: {ingredients.join(", ")}
        </p>
      )}

      {matches.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "var(--gray-50)", textAlign: "left" }}>
                <th style={{ padding: 12 }}>Dish</th><th>Restaurant</th><th>Price</th><th>Match</th><th></th>
              </tr>
            </thead>
            <tbody>
              {matches.map((m) => (
                <tr key={m.food_id} style={{ borderTop: "1px solid var(--gray-100)" }}>
                  <td style={{ padding: 12 }}>{m.food_name}</td>
                  <td>{m.restaurant_name}</td>
                  <td>₹{m.price}</td>
                  <td>{m.match_percent}%</td>
                  <td>
                    <button className="btn btn-primary btn-sm" disabled={!m.is_available || addingId === m.food_id} onClick={() => handleAdd(m)}>
                      {addingId === m.food_id ? "..." : m.is_available ? "Add +" : "Unavailable"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}