import { useEffect, useState } from "react";
import { getNutritionSummary, exportNutritionData } from "../../services/endpoints";

export default function NutritionPage() {
  const [range, setRange] = useState("daily");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    setLoading(true);
    getNutritionSummary(range)
      .then((res) => setSummary(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [range]);

  async function handleExport() {
    setExporting(true);
    try {
      const res = await exportNutritionData();
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "my-nutrition-data.json";
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 700 }}>
      <h2 style={{ marginTop: 0 }}>📊 Nutrition Tracking</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Optional summary from restaurant-provided nutrition estimates on your orders.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <button className={`btn btn-sm ${range === "daily" ? "btn-primary" : "btn-outline"}`} onClick={() => setRange("daily")}>Today</button>
        <button className={`btn btn-sm ${range === "weekly" ? "btn-primary" : "btn-outline"}`} onClick={() => setRange("weekly")}>This Week</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="skeleton" style={{ height: 160 }} />
      ) : summary ? (
        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, textAlign: "center" }}>
            <div><div style={{ fontSize: 24, fontWeight: 700 }}>{summary.calories}</div><div style={{ fontSize: 12, color: "var(--gray-500)" }}>kcal</div></div>
            <div><div style={{ fontSize: 24, fontWeight: 700 }}>{summary.protein_grams}g</div><div style={{ fontSize: 12, color: "var(--gray-500)" }}>Protein</div></div>
            <div><div style={{ fontSize: 24, fontWeight: 700 }}>{summary.carbs_grams}g</div><div style={{ fontSize: 12, color: "var(--gray-500)" }}>Carbs</div></div>
            <div><div style={{ fontSize: 24, fontWeight: 700 }}>{summary.fat_grams}g</div><div style={{ fontSize: 12, color: "var(--gray-500)" }}>Fat</div></div>
          </div>
          <p style={{ fontSize: 12, color: "var(--gray-500)", textAlign: "center", marginTop: 14 }}>
            From {summary.order_count} logged order{summary.order_count === 1 ? "" : "s"}.
          </p>
          <p style={{ fontSize: 11, color: "var(--gray-500)", marginTop: 8 }}>{summary.disclaimer}</p>
        </div>
      ) : null}

      <button className="btn btn-outline" style={{ marginTop: 16 }} disabled={exporting} onClick={handleExport}>
        {exporting ? "Exporting..." : "Export My Nutrition Data"}
      </button>
    </div>
  );
}