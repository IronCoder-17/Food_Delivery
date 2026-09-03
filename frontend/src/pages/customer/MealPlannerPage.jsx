import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createMealPlan, buildCartFromMealPlan } from "../../services/endpoints";
import { useCart } from "../../hooks/CartContext";

const DAY_NAMES = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7", "Day 8", "Day 9", "Day 10", "Day 11", "Day 12", "Day 13", "Day 14"];

export default function MealPlannerPage() {
  const { refreshCart } = useCart();
  const navigate = useNavigate();

  const [form, setForm] = useState({ days: 5, meals_per_day: 1, budget: "", is_veg: "", max_spend_per_meal: "" });
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [generating, setGenerating] = useState(false);

  const [buildResult, setBuildResult] = useState(null);
  const [building, setBuilding] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleGenerate(e) {
    e.preventDefault();
    setError("");
    setPlan(null);
    setBuildResult(null);
    setGenerating(true);
    try {
      const payload = {
        days: parseInt(form.days, 10),
        meals_per_day: parseInt(form.meals_per_day, 10),
      };
      if (form.budget) payload.budget = parseFloat(form.budget);
      if (form.is_veg !== "") payload.is_veg = form.is_veg === "true";
      if (form.max_spend_per_meal) payload.max_spend_per_meal = parseFloat(form.max_spend_per_meal);

      const res = await createMealPlan(payload);
      setPlan(res.data);
    } catch (err) {
      setError(err.message || "Failed to generate meal plan.");
    } finally {
      setGenerating(false);
    }
  }

  async function handleBuildCart() {
    if (!plan) return;
    setBuilding(true);
    setBuildResult(null);
    try {
      const res = await buildCartFromMealPlan(plan.id);
      setBuildResult(res.data);
      await refreshCart();
    } catch (err) {
      setBuildResult({ added: [], skipped: [], error: err.message });
    } finally {
      setBuilding(false);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 820 }}>
      <h2>🧠 AI Meal Planner</h2>
      <p style={{ color: "var(--gray-500)", marginTop: 4 }}>
        Tell us your days, budget, and preferences — we'll build a weekly plan using real dishes
        currently available on QuickBite, and re-check price &amp; availability again before adding anything to your cart.
      </p>

      <form onSubmit={handleGenerate} className="card" style={{ padding: 20, marginBottom: 20 }}>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="grid grid-2">
          <div className="field">
            <label>Number of Days</label>
            <input className="input" type="number" min="1" max="14" value={form.days} onChange={(e) => update("days", e.target.value)} />
          </div>
          <div className="field">
            <label>Meals per Day</label>
            <select className="input" value={form.meals_per_day} onChange={(e) => update("meals_per_day", e.target.value)}>
              <option value="1">1 (e.g. Dinner only)</option>
              <option value="2">2 (Lunch + Dinner)</option>
              <option value="3">3 (Breakfast + Lunch + Dinner)</option>
            </select>
          </div>
        </div>
        <div className="grid grid-2">
          <div className="field">
            <label>Total Budget (₹, optional)</label>
            <input className="input" type="number" min="1" value={form.budget} onChange={(e) => update("budget", e.target.value)} placeholder="e.g. 1500" />
          </div>
          <div className="field">
            <label>Max Spend per Meal (₹, optional)</label>
            <input className="input" type="number" min="1" value={form.max_spend_per_meal} onChange={(e) => update("max_spend_per_meal", e.target.value)} placeholder="e.g. 200" />
          </div>
        </div>
        <div className="field">
          <label>Dietary Preference</label>
          <select className="input" value={form.is_veg} onChange={(e) => update("is_veg", e.target.value)}>
            <option value="">No preference</option>
            <option value="true">Vegetarian</option>
            <option value="false">Non-Vegetarian</option>
          </select>
        </div>
        <button className="btn btn-primary" disabled={generating}>{generating ? "Planning..." : "Generate Plan"}</button>
      </form>

      {plan && (
        <div className="card" style={{ padding: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
            <div>
              <h3 style={{ margin: 0 }}>{plan.restaurant_name || "Meal Plan"}</h3>
              <p style={{ margin: "4px 0 0", color: "var(--gray-700)" }}>{plan.summary_note}</p>
            </div>
            <button className="btn btn-primary" disabled={building} onClick={handleBuildCart}>
              {building ? "Adding..." : "🛒 Build Cart"}
            </button>
          </div>

          {buildResult && (
            <div className="card" style={{ padding: 14, marginTop: 14, background: "var(--gray-50, #fafafa)" }}>
              {buildResult.error && <div className="alert alert-error">{buildResult.error}</div>}
              {buildResult.added?.length > 0 && (
                <div style={{ fontSize: 13.5, color: "var(--green)", marginBottom: 4 }}>
                  ✓ Added: {buildResult.added.map((a) => `${a.name} (₹${a.current_price})`).join(", ")}
                </div>
              )}
              {buildResult.skipped?.length > 0 && (
                <div style={{ fontSize: 13.5, color: "var(--red)" }}>
                  Skipped: {buildResult.skipped.map((s) => `${s.meal_label} — ${s.reason}`).join("; ")}
                </div>
              )}
              {buildResult.added?.length > 0 && (
                <button className="btn btn-primary btn-sm" style={{ marginTop: 8 }} onClick={() => navigate("/cart")}>Go to Cart</button>
              )}
            </div>
          )}

          <div style={{ marginTop: 18 }}>
            {plan.schedule.map((day) => (
              <div key={day.day_index} style={{ borderTop: "1px solid var(--gray-100)", padding: "12px 0" }}>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>{DAY_NAMES[day.day_index] || `Day ${day.day_index + 1}`}</div>
                {day.items.map((item) => (
                  <div key={item.meal_index} style={{ display: "flex", justifyContent: "space-between", fontSize: 14, padding: "3px 0" }}>
                    <span>
                      <strong>{item.meal_label}:</strong>{" "}
                      {item.food_name ? `${item.food_name} × ${item.quantity}` : <span style={{ color: "var(--red)" }}>{item.unavailable_reason}</span>}
                    </span>
                    {item.price != null && <span>₹{item.price}</span>}
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div style={{ textAlign: "right", fontWeight: 700, marginTop: 12, fontSize: 16 }}>
            Estimated Total: ₹{plan.estimated_total}
          </div>
        </div>
      )}
    </div>
  );
}
