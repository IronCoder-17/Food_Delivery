import { useRef, useState } from "react";
import { matchDishFromPhoto, matchDishFromName, addToCart as addToCartApi } from "../../services/endpoints";
import { useCart } from "../../hooks/CartContext";

const MAX_FILE_BYTES = 5 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default function PhotoReorderPage() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [manualDishName, setManualDishName] = useState("");
  const [showManual, setShowManual] = useState(false);
  const [nearbyOnly, setNearbyOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [dishName, setDishName] = useState("");
  const [ingredients, setIngredients] = useState([]);
  const [nearbyApplied, setNearbyApplied] = useState(false);
  const [matches, setMatches] = useState([]);
  const [addingId, setAddingId] = useState(null);
  const [toast, setToast] = useState("");
  const fileInputRef = useRef(null);
  const { refreshCart } = useCart();

  function resetResults() {
    setError(""); setInfo(""); setDishName(""); setIngredients([]); setMatches([]); setNearbyApplied(false);
  }

  function handleFileChange(e) {
    const picked = e.target.files?.[0];
    resetResults();
    if (!picked) {
      setFile(null); setPreviewUrl("");
      return;
    }
    if (!ALLOWED_TYPES.includes(picked.type)) {
      setError("Unsupported image type. Please choose a JPEG, PNG, or WEBP photo.");
      setFile(null); setPreviewUrl("");
      return;
    }
    if (picked.size > MAX_FILE_BYTES) {
      setError("Image is too large (max 5 MB).");
      setFile(null); setPreviewUrl("");
      return;
    }
    setFile(picked);
    setPreviewUrl(URL.createObjectURL(picked));
  }

  async function handlePhotoSubmit(e) {
    e.preventDefault();
    resetResults();
    if (!file) {
      setError("Choose a photo first.");
      return;
    }
    setLoading(true);
    try {
      const res = await matchDishFromPhoto(file, nearbyOnly);
      if (res.data.needs_manual_input) {
        setInfo(res.data.error || "Couldn't identify that photo automatically.");
      } else {
        applyResult(res.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleManualSubmit(e) {
    e.preventDefault();
    resetResults();
    if (!manualDishName.trim()) {
      setError("Enter a dish name.");
      return;
    }
    setLoading(true);
    try {
      const res = await matchDishFromName(manualDishName.trim(), nearbyOnly);
      applyResult(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function applyResult(data) {
    setDishName(data.dish_name || "");
    setIngredients(data.ingredients || []);
    setMatches(data.matches || []);
    setNearbyApplied(!!data.nearby_applied);
    if ((data.matches || []).length === 0) {
      setInfo("No matching dishes found on the menu right now.");
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
      <h2 style={{ marginTop: 0 }}>Photo Reorder</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Snap or upload a photo of a dish -- yours, a friend's, or from anywhere -- and we'll find the
        closest matching dishes on the menu.
      </p>

      <form onSubmit={handlePhotoSubmit} className="card" style={{ padding: 18, marginBottom: 14 }}>
        <div className="field">
          <label>Dish photo</label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="input"
            onChange={handleFileChange}
          />
          <div className="hint">JPEG, PNG, or WEBP, up to 5 MB.</div>
        </div>

        {previewUrl && (
          <img
            src={previewUrl}
            alt="Selected dish preview"
            style={{ width: "100%", maxHeight: 260, objectFit: "cover", borderRadius: "var(--radius)", marginBottom: 14, border: "1px solid var(--gray-100)" }}
          />
        )}

        <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14, fontSize: 14.5 }}>
          <input type="checkbox" checked={nearbyOnly} onChange={(e) => setNearbyOnly(e.target.checked)} />
          Prefer restaurants in my city
        </label>

        <button className="btn btn-primary" disabled={loading || !file}>
          {loading ? "Identifying dish..." : "Find Matching Dishes"}
        </button>
      </form>

      <button className="btn btn-ghost btn-sm" onClick={() => setShowManual((v) => !v)} style={{ marginBottom: 10 }}>
        {showManual ? "Hide" : "Or type the dish name instead"}
      </button>

      {showManual && (
        <form onSubmit={handleManualSubmit} className="card" style={{ padding: 18, marginBottom: 14 }}>
          <div className="field">
            <label>Dish name</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input className="input" value={manualDishName} onChange={(e) => setManualDishName(e.target.value)} placeholder="Margherita Pizza" />
              <button className="btn btn-primary" disabled={loading}>{loading ? "Working..." : "Match"}</button>
            </div>
          </div>
        </form>
      )}

      {toast && <div className="alert alert-success">{toast}</div>}
      {error && <div className="alert alert-error">{error}</div>}
      {info && <div className="alert alert-info">{info}</div>}

      {dishName && (
        <p style={{ fontSize: 14.5 }}>
          Looks like: <strong>{dishName}</strong>
          {ingredients.length > 0 && (
            <span style={{ color: "var(--gray-500)" }}> &middot; likely ingredients: {ingredients.join(", ")}</span>
          )}
        </p>
      )}

      {matches.length > 0 && nearbyApplied && (
        <p style={{ fontSize: 13, color: "var(--gray-500)" }}>Showing restaurants in your city first.</p>
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
