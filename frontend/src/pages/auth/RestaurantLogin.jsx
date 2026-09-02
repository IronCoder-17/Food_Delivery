import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { restaurantLogin } from "../../services/endpoints";
import { useAuth } from "../../hooks/AuthContext";
import ThemeToggle from "../../components/ThemeToggle";

export default function RestaurantLogin() {
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
      const res = await restaurantLogin(email, password);
      login(res.data.token, res.data.user);
      navigate("/restaurant");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", padding: "0 20px" }}>
      <ThemeToggle variant="floating" />
      <div className="card" style={{ padding: 32 }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Restaurant Login</h2>
        <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 24 }}>Manage your menu and orders.</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Restaurant Email</label>
            <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : "Log In"}
          </button>
        </form>
        <div style={{ textAlign: "center", marginTop: 16, fontSize: 14.5 }}>
          New restaurant? <Link to="/restaurant/register">Apply here</Link>
        </div>
      </div>
    </div>
  );
}
