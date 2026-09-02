export default function StatCard({ label, value, accent }) {
  return (
    <div className="card" style={{ padding: "18px 20px" }}>
      <div style={{ fontSize: 13.5, color: "var(--gray-500)", fontWeight: 700, marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: accent ? "var(--orange)" : "var(--ink)" }}>{value}</div>
    </div>
  );
}
