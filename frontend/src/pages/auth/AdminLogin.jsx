import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminLogin } from "../../services/endpoints";
import { useAuth } from "../../hooks/AuthContext";
import ThemeToggle from "../../components/ThemeToggle";

const darkInputStyle = { background: "var(--surface-fixed-light)", color: "var(--text-fixed-dark)", borderColor: "#555" };

export default function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await adminLogin(email, password);
      login(res.data.token, res.data.user);
      navigate("/admin");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "100px auto", padding: "0 20px" }}>
      <ThemeToggle variant="floating" />
      <div className="card" style={{ padding: 32, background: "var(--ink-static)", color: "#fff" }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Admin Login</h2>
        <p style={{ textAlign: "center", color: "#ccc", marginBottom: 24, fontSize: 13.5 }}>Restricted access — authorized personnel only.</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label style={{ color: "#ccc" }}>Admin Email</label>
            <input className="input" style={darkInputStyle} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="field">
            <label style={{ color: "#ccc" }}>Admin Password</label>
            <input className="input" style={darkInputStyle} type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : "Log In"}
          </button>
        </form>
      </div>
    </div>
  );
}
