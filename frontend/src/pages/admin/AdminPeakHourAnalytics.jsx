import { useEffect, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { getPeakHourAnalytics } from "../../services/endpoints";
import StatCard from "../../components/StatCard";
import ChartCard from "../../components/ChartCard";

const RANGES = [
  { key: "today", label: "Today" },
  { key: "7d", label: "7 Days" },
  { key: "30d", label: "30 Days" },
];

export default function AdminPeakHourAnalytics() {
  const [range, setRange] = useState("7d");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    getPeakHourAnalytics(range)
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [range]);

  return (
    <div>
      <h2>⏱️ Peak-Hour Analytics</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {RANGES.map((r) => (
          <button key={r.key} className={`btn btn-sm ${range === r.key ? "btn-primary" : "btn-outline"}`} onClick={() => setRange(r.key)}>
            {r.label}
          </button>
        ))}
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {data && (
        <div className="grid grid-3" style={{ marginBottom: 20 }}>
          <StatCard label="Total Orders" value={data.total_orders} />
          <StatCard label="Total Revenue" value={`₹${data.total_revenue.toLocaleString("en-IN")}`} />
          <StatCard label="Average Order Value" value={`₹${data.average_order_value}`} />
        </div>
      )}

      <ChartCard title="Orders by Hour of Day" loading={loading} empty={!data?.orders_by_hour?.some((h) => h.orders > 0)}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data?.orders_by_hour || []} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
            <XAxis dataKey="hour" tick={{ fontSize: 11, fill: "var(--gray-500)" }} />
            <YAxis tick={{ fontSize: 12, fill: "var(--gray-500)" }} allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="orders" name="Orders" fill="var(--orange)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Revenue by Hour of Day" loading={loading} empty={!data?.revenue_by_hour?.some((h) => h.revenue > 0)}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data?.revenue_by_hour || []} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
            <XAxis dataKey="hour" tick={{ fontSize: 11, fill: "var(--gray-500)" }} />
            <YAxis tick={{ fontSize: 12, fill: "var(--gray-500)" }} tickFormatter={(v) => `₹${v}`} />
            <Tooltip formatter={(v) => `₹${v}`} />
            <Line type="monotone" dataKey="revenue" name="Revenue" stroke="var(--ink)" strokeWidth={2.5} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Orders by Day" loading={loading} empty={!data?.orders_by_day?.length}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data?.orders_by_day || []} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: "var(--gray-500)" }} />
            <YAxis tick={{ fontSize: 12, fill: "var(--gray-500)" }} allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="orders" name="Orders" fill="var(--orange-dark)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {data?.peak_hours?.length > 0 && (
        <div className="card" style={{ padding: 16, marginTop: 16 }}>
          <strong>Peak Hour{data.peak_hours.length > 1 ? "s" : ""}: {data.peak_hours.map((h) => `${h}:00`).join(", ")}</strong>
          <div className="grid grid-2" style={{ marginTop: 12 }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Popular Foods at Peak</div>
              {data.popular_foods_at_peak.map((f, i) => (
                <div key={i} style={{ fontSize: 13.5, padding: "3px 0" }}>{f.food_name} — {f.quantity} sold</div>
              ))}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Popular Restaurants at Peak</div>
              {data.popular_restaurants_at_peak.map((r, i) => (
                <div key={i} style={{ fontSize: 13.5, padding: "3px 0" }}>{r.restaurant_name} — {r.orders} orders</div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
