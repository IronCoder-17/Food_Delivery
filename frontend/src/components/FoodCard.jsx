export default function FoodCard({ food, onAdd, isFavorite, onToggleFavorite }) {
  const hasDiscount = food.discount_percent > 0;
  const dealSource = food.flash_sale?.source; // "flash_sale" | "chef_special"
  const hasFlashSale = dealSource === "flash_sale";
  const hasChefSpecial = dealSource === "chef_special";
  const displayPrice = food.effective_price ?? food.final_price;
  const soldOut = !food.is_available;
  const allergens = food.allergens || [];
  const moods = food.moods || [];

  return (
    <div className="card" style={{ overflow: "hidden", display: "flex", flexDirection: "column", opacity: soldOut ? 0.65 : 1 }}>
      <div style={{ height: 140, background: "var(--orange-light)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 40, position: "relative" }}>
        {food.image_url ? <img src={food.image_url} alt={food.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : "🍛"}
        {onToggleFavorite && (
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); onToggleFavorite(food); }}
            aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
            style={{
              position: "absolute", top: 8, right: 8, width: 30, height: 30, borderRadius: "50%",
              border: "none", background: "rgba(255,255,255,0.9)", cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 15,
              boxShadow: "0 1px 4px rgba(0,0,0,0.25)",
            }}
          >
            {isFavorite ? "❤️" : "🤍"}
          </button>
        )}
        {hasChefSpecial && !soldOut && (
          <span style={{
            position: "absolute", top: 8, left: 8, background: "#7b2cbf", color: "#fff",
            fontSize: 11.5, fontWeight: 700, padding: "3px 8px", borderRadius: 6,
          }}>
            👨‍🍳 Chef's Special
          </span>
        )}
        {hasFlashSale && !soldOut && (
          <span style={{
            position: "absolute", top: 8, left: 8, background: "#e63946", color: "#fff",
            fontSize: 11.5, fontWeight: 700, padding: "3px 8px", borderRadius: 6,
          }}>
            🔥 Flash Sale -{food.flash_sale.discount_percent}%
          </span>
        )}
        {soldOut && (
          <span style={{
            position: "absolute", top: 8, left: 8, background: "var(--ink, #222)", color: "#fff",
            fontSize: 11.5, fontWeight: 700, padding: "3px 8px", borderRadius: 6,
          }}>
            Sold Out
          </span>
        )}
        {!soldOut && food.is_low_stock && !hasFlashSale && !hasChefSpecial && (
          <span style={{
            position: "absolute", top: 8, left: 8, background: "#f5a623", color: "#fff",
            fontSize: 11.5, fontWeight: 700, padding: "3px 8px", borderRadius: 6,
          }}>
            Low Stock
          </span>
        )}
      </div>
      <div style={{ padding: 14, flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
          <span className={`badge ${food.is_veg ? "badge-veg" : "badge-nonveg"}`}>{food.is_veg ? "● Veg" : "● Non-Veg"}</span>
          {food.rating > 0 && <span style={{ fontSize: 13, color: "var(--gray-500)" }}>⭐ {food.rating}</span>}
        </div>
        <h4 style={{ margin: "8px 0 2px" }}>{food.name}</h4>
        <div style={{ fontSize: 13, color: "var(--gray-500)", marginBottom: 6 }}>{food.restaurant_name}</div>
        {(moods.length > 0 || allergens.length > 0) && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 8 }}>
            {moods.map((m) => (
              <span key={`mood-${m.id}`} style={{
                fontSize: 11, background: "var(--orange-light, #ffe8d6)", color: "var(--orange, #d35400)",
                padding: "2px 7px", borderRadius: 10, fontWeight: 600,
              }} title="Mood tag">{m.emoji} {m.name}</span>
            ))}
            {allergens.map((a) => (
              <span key={`allergen-${a.id}`} style={{
                fontSize: 11, background: "#eef1f5", color: "#445", padding: "2px 7px", borderRadius: 10, fontWeight: 600,
              }} title="Restaurant-provided ingredient/allergen info -- confirm directly with the restaurant if you have allergies.">
                {a.name}
              </span>
            ))}
          </div>
        )}
        <p style={{ fontSize: 13.5, color: "var(--gray-700)", flex: 1, marginBottom: 10 }}>
          {food.description?.slice(0, 70)}{food.description?.length > 70 ? "…" : ""}
        </p>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <span style={{ fontWeight: 700, fontSize: 17 }}>₹{displayPrice}</span>
            {(hasDiscount || hasFlashSale || hasChefSpecial) && (
              <span style={{ marginLeft: 6, fontSize: 13, color: "var(--gray-500)", textDecoration: "line-through" }}>
                ₹{food.price}
              </span>
            )}
          </div>
          <button className="btn btn-primary btn-sm" disabled={soldOut} onClick={() => onAdd(food)}>
            {soldOut ? "Sold out" : "Add +"}
          </button>
        </div>
      </div>
    </div>
  );
}
