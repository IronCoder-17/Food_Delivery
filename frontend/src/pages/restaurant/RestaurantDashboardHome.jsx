import { useEffect, useState } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { getRestaurantDashboard, getRestaurantAnalytics } from "../../services/endpoints";
import StatCard from "../../components/StatCard";
import ChartCard from "../../components/ChartCard";

const PIE_COLORS = ["#E4602A", "#2E7D32", "#4A443C", "#C24A1B", "#8B8478", "#C62828", "#E8A75D", "#6E7A4B"];

const currency = (v) => `₹${Number(v).toLocaleString("en-IN")}`;

function RevenueTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--white)", border: "1px solid var(--gray-300)", borderRadius: 8, padding: "8px 12px", boxShadow: "var(--shadow)" }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      <div>Revenue: {currency(payload[0].value)}</div>
    </div>
  );
}

function CustomersTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--white)", border: "1px solid var(--gray-300)", borderRadius: 8, padding: "8px 12px", boxShadow: "var(--shadow)" }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      <div>Customers: {payload.find((p) => p.dataKey === "customers")?.value ?? 0}</div>
      <div>Orders: {payload.find((p) => p.dataKey === "orders")?.value ?? 0}</div>
    </div>
  );
}

function CategoryTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { category, orders, percent } = payload[0].payload;
  return (
    <div style={{ background: "var(--white)", border: "1px solid var(--gray-300)", borderRadius: 8, padding: "8px 12px", boxShadow: "var(--shadow)" }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{category}</div>
      <div>{orders} ordered ({percent}%)</div>
    </div>
  );
}

export default function RestaurantDashboardHome() {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);
  const [analyticsError, setAnalyticsError] = useState("");

  useEffect(() => { getRestaurantDashboard().then((res) => setStats(res.data)); }, []);

  useEffect(() => {
    setLoadingAnalytics(true);
    getRestaurantAnalytics()
      .then((res) => { setAnalytics(res.data); setAnalyticsError(""); })
      .catch((err) => setAnalyticsError(err.message || "Failed to load analytics."))
      .finally(() => setLoadingAnalytics(false));
  }, []);

  const categoryData = (analytics?.food_categories || []).map((c) => {
    const total = (analytics?.food_categories || []).reduce((sum, x) => sum + x.orders, 0) || 1;
    return { ...c, percent: Math.round((c.orders / total) * 100) };
  });

  if (!stats) return <div className="skeleton" style={{ height: 200 }} />;

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="grid grid-4" style={{ marginBottom: 10 }}>
        <StatCard label="Total Orders" value={stats.total_orders} />
        <StatCard label="Today's Orders" value={stats.today_orders} accent />
        <StatCard label="Pending Orders" value={stats.pending_orders} />
        <StatCard label="Completed Orders" value={stats.completed_orders} />
        <StatCard label="Total Food Items" value={stats.total_food_items} />
        <StatCard label="Available Items" value={stats.available_food_items} />
        <StatCard label="Total Revenue" value={currency(stats.total_revenue)} accent />
      </div>

      <h3 style={{ marginTop: 26, marginBottom: 6 }}>Analytics</h3>
      {analyticsError && <div className="alert alert-error" style={{ marginBottom: 16 }}>{analyticsError}</div>}

      <ChartCard title="Monthly Revenue" loading={loadingAnalytics} empty={!analyticsError && (analytics?.monthly_revenue || []).length === 0}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={analytics?.monthly_revenue || []} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: "var(--gray-500)" }} />
            <YAxis tick={{ fontSize: 12, fill: "var(--gray-500)" }} tickFormatter={(v) => `₹${v}`} />
            <Tooltip content={<RevenueTooltip />} />
            <Line type="monotone" dataKey="revenue" name="Revenue" stroke="var(--orange)" strokeWidth={2.5} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Monthly Customers & Orders" loading={loadingAnalytics} empty={!analyticsError && (analytics?.monthly_customers || []).length === 0}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={analytics?.monthly_customers || []} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: "var(--gray-500)" }} />
            <YAxis tick={{ fontSize: 12, fill: "var(--gray-500)" }} allowDecimals={false} />
            <Tooltip content={<CustomersTooltip />} />
            <Legend />
            <Bar dataKey="customers" name="Customers" fill="var(--orange)" radius={[6, 6, 0, 0]} />
            <Bar dataKey="orders" name="Orders" fill="var(--ink)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Most Ordered Food Categories" loading={loadingAnalytics} empty={!analyticsError && categoryData.length === 0}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={categoryData} dataKey="orders" nameKey="category" cx="50%" cy="50%" outerRadius={95} innerRadius={50} paddingAngle={2}>
              {categoryData.map((entry, i) => (
                <Cell key={entry.category} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CategoryTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
