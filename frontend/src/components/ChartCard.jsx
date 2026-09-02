export default function ChartCard({ title, loading, empty, children, height = 300 }) {
  return (
    <div className="card" style={{ padding: "18px 20px 12px", marginBottom: 20 }}>
      <div style={{ fontSize: 15.5, fontWeight: 700, marginBottom: 14 }}>{title}</div>
      {loading ? (
        <div className="skeleton" style={{ height }} />
      ) : empty ? (
        <div
          style={{
            height,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--gray-500)",
            fontSize: 14.5,
          }}
        >
          No data available
        </div>
      ) : (
        <div style={{ width: "100%", height }}>{children}</div>
      )}
    </div>
  );
}
