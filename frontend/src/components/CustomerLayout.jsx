import { Outlet } from "react-router-dom";
import CustomerNavbar from "../components/CustomerNavbar";

export default function CustomerLayout() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <CustomerNavbar />
      <div style={{ flex: 1 }}>
        <Outlet />
      </div>
      <footer style={{ background: "var(--ink-static)", color: "#ccc", padding: "24px 20px", textAlign: "center", fontSize: 13.5, marginTop: 40 }}>
        © {new Date().getFullYear()} QuickBite. All rights reserved.
      </footer>
    </div>
  );
}
