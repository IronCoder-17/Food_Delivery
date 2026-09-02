import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/AuthContext";
import ThemeToggle from "./ThemeToggle";

export default function DashboardLayout({ title, links, children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={{
        width: 230, background: "var(--ink-static)", color: "#fff", padding: "22px 16px 16px",
        display: "flex", flexDirection: "column", position: "sticky", top: 0, height: "100vh",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, marginBottom: 26, flexShrink: 0 }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: "var(--orange)" }}>
            🍽️ {title}
          </div>
          <ThemeToggle variant="sidebar" />
        </div>
        <nav style={{
          display: "flex", flexDirection: "column", gap: 4,
          flex: "1 1 auto", minHeight: 0, overflowY: "auto", paddingRight: 4,
        }}>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              style={({ isActive }) => ({
                padding: "10px 12px", borderRadius: 8, color: "#fff", textDecoration: "none",
                background: isActive ? "var(--orange)" : "transparent", fontWeight: isActive ? 700 : 400,
                flexShrink: 0,
              })}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ borderTop: "1px solid #444", paddingTop: 14, marginTop: 14, flexShrink: 0 }}>
          <div style={{ fontSize: 13.5, opacity: 0.8, marginBottom: 10 }}>{user?.name}</div>
          <button className="btn btn-outline btn-sm btn-block" style={{ borderColor: "#666", color: "#fff" }}
            onClick={() => { logout(); navigate("/"); }}>
            Logout
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, background: "var(--gray-50)", minHeight: "100vh" }}>
        <div style={{ padding: "26px 30px" }}>{children}</div>
      </main>
    </div>
  );
}
