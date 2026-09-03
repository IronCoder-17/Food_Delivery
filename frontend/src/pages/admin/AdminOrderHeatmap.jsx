import { useEffect, useState } from "react";
import { getOrderHeatmap } from "../../services/endpoints";

const RANGES = [
  { key: "today", label: "Today" },
  { key: "7d", label: "7 Days" },
  { key: "30d", label: "30 Days" },
];

export default function AdminOrderHeatmap() {
  const [range, setRange] = useState("7d");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    getOrderHeatmap(range)
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [range]);

  const maxCount = data?.cities?.[0]?.order_count || 1;

  return (
    <div>
      <h2>🗺️ Order Density Heatmap</h2>
      <p style={{ color: "var(--gray-500)" }}>
        Aggregated by city/pincode -- individual customer addresses are never shown here.
      </p>
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {RANGES.map((r) => (
          <button key={r.key} className={`btn btn-sm ${range === r.key ? "btn-primary" : "btn-outline"}`} onClick={() => setRange(r.key)}>
            {r.label}
          </button>
        ))}
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="skeleton" style={{ height: 300 }} />
      ) : (
        <>
          {data?.coverage_note && (
            <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginBottom: 16 }}>{data.coverage_note}</div>
          )}

          <div className="grid grid-2">
            <div className="card" style={{ padding: 16 }}>
              <strong>High-Order Cities</strong>
              {data?.cities?.length === 0 && <div className="empty-state" style={{ padding: 20 }}><p>No structured location data in this range.</p></div>}
              {data?.cities?.map((c) => (
                <div key={c.city_id} style={{ margin: "10px 0" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5 }}>
                    <span>{c.city_name || `City #${c.city_id}`}</span>
                    <strong>{c.order_count}</strong>
                  </div>
                  <div style={{ height: 8, background: "var(--gray-100)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${(c.order_count / maxCount) * 100}%`, background: "var(--orange)" }} />
                  </div>
                </div>
              ))}
            </div>

            <div className="card" style={{ padding: 16 }}>
              <strong>Top Pincodes</strong>
              {data?.pincodes?.length === 0 && <div className="empty-state" style={{ padding: 20 }}><p>No pincode data in this range.</p></div>}
              {data?.pincodes?.map((p) => (
                <div key={p.pincode} style={{ display: "flex", justifyContent: "space-between", fontSize: 13.5, padding: "4px 0" }}>
                  <span>{p.pincode}</span><span>{p.order_count} orders</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
