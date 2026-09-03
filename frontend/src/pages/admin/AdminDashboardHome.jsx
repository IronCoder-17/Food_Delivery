import { useEffect, useState } from "react";
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { getAdminDashboard, getAdminAnalytics } from "../../services/endpoints";
import StatCard from "../../components/StatCard";
import ChartCard from "../../components/ChartCard";

const currency = (v) => `₹${Number(v).toLocaleString("en-IN")}`;

function CustomersTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--white)", border: "1px solid var(--gray-300)", borderRadius: 8, padding: "8px 12px", boxShadow: "var(--shadow)" }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      <div>New Customers: {payload[0].value}</div>
    </div>
  );
}

function RevenueTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--white)", border: "1px solid var(--gray-300)", borderRadius: 8, padding: "8px 12px", boxShadow: "var(--shadow)" }}>
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{label}</div>
      <div>Total Revenue: {currency(payload[0].value)}</div>
    </div>
  );
}

export default function AdminDashboardHome() {
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);
  const [analyticsError, setAnalyticsError] = useState("");

  useEffect(() => { getAdminDashboard().then((res) => setStats(res.data)); }, []);

  useEffect(() => {
    setLoadingAnalytics(true);
    getAdminAnalytics()
      .then((res) => { setAnalytics(res.data); setAnalyticsError(""); })
      .catch((err) => setAnalyticsError(err.message || "Failed to load analytics."))
      .finally(() => setLoadingAnalytics(false));
  }, []);

  if (!stats) return <div className="skeleton" style={{ height: 200 }} />;

  return (
    <div>
      <h2>Admin Dashboard</h2>
      <div className="grid grid-4">
        <StatCard label="Total Customers" value={stats.total_customers} />
        <StatCard label="Total Restaurants" value={stats.total_restaurants} />
        <StatCard label="Pending Restaurants" value={stats.pending_restaurants} accent />
        <StatCard label="Total Food Items" value={stats.total_food_items} />
        <StatCard label="Total Orders" value={stats.total_orders} />
        <StatCard label="Today's Orders" value={stats.today_orders} accent />
        <StatCard label="Total Revenue" value={`₹${stats.total_revenue}`} accent />
        <StatCard label="Wallet Bonuses Paid" value={`₹${stats.wallet_bonuses_paid}`} />
        <StatCard label="Active Users" value={stats.active_users} />
      </div>

      <h3 style={{ marginTop: 26 }}>Payment Statistics</h3>
      <div className="grid grid-4">
        <StatCard label="Razorpay (Success)" value={stats.payment_stats.razorpay} />
        <StatCard label="Cash on Delivery" value={stats.payment_stats.cod} />
        <StatCard label="Wallet (Success)" value={stats.payment_stats.wallet} />
        <StatCard label="Failed" value={stats.payment_stats.failed} />
      </div>

      <h3 style={{ marginTop: 26, marginBottom: 6 }}>Platform Analytics</h3>
      {analyticsError && <div className="alert alert-error" style={{ marginBottom: 16 }}>{analyticsError}</div>}

      <ChartCard title="Customer Growth by Month" loading={loadingAnalytics} empty={!analyticsError && (analytics?.monthly_customers || []).length === 0}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={analytics?.monthly_customers || []} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: "var(--gray-500)" }} />
            <YAxis tick={{ fontSize: 12, fill: "var(--gray-500)" }} allowDecimals={false} />
            <Tooltip content={<CustomersTooltip />} />
            <Legend />
            <Bar dataKey="customers" name="New Customers" fill="var(--orange)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Total Revenue – All Restaurants" loading={loadingAnalytics} empty={!analyticsError && (analytics?.monthly_revenue || []).length === 0}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={analytics?.monthly_revenue || []} margin={{ top: 8, right: 20, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: "var(--gray-500)" }} />
            <YAxis tick={{ fontSize: 12, fill: "var(--gray-500)" }} tickFormatter={(v) => `₹${v}`} />
            <Tooltip content={<RevenueTooltip />} />
            <Legend />
            <Line type="monotone" dataKey="revenue" name="Total Revenue" stroke="var(--ink)" strokeWidth={2.5} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
