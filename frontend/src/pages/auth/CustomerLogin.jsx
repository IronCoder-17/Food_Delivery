import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import { customerLogin, customerGoogleLogin } from "../../services/endpoints";
import { useAuth } from "../../hooks/AuthContext";

const GOOGLE_CONFIGURED = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);

export default function CustomerLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  function routeAfterLogin(user) {
    if (user?.needs_profile_completion) {
      navigate("/complete-profile");
    } else {
      navigate("/");
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await customerLogin(email, password);
      login(res.data.token, res.data.user);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSuccess(credentialResponse) {
    if (googleLoading) return; // guard against duplicate/rapid callbacks
    setError("");
    if (!credentialResponse?.credential) {
      setError("Google sign-in did not return a credential. Please try again.");
      return;
    }
    setGoogleLoading(true);
    try {
      const res = await customerGoogleLogin(credentialResponse.credential);
      login(res.data.token, res.data.user);
      routeAfterLogin(res.data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setGoogleLoading(false);
    }
  }

  function handleGoogleError() {
    setError("Google sign-in was cancelled or failed. Please try again.");
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 32 }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Customer Login</h2>
        <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 24 }}>Welcome back! Log in to order your favorites.</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email Address</label>
            <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading || googleLoading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : "Log In"}
          </button>
        </form>

        {GOOGLE_CONFIGURED && (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0" }}>
              <div style={{ flex: 1, height: 1, background: "var(--gray-200, #e5e7eb)" }} />
              <span style={{ color: "var(--gray-500)", fontSize: 13 }}>OR</span>
              <div style={{ flex: 1, height: 1, background: "var(--gray-200, #e5e7eb)" }} />
            </div>

            <div
              style={{ display: "flex", justifyContent: "center", opacity: googleLoading ? 0.6 : 1, pointerEvents: googleLoading ? "none" : "auto" }}
              aria-busy={googleLoading}
            >
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                useOneTap={false}
                shape="rectangular"
                theme="outline"
                size="large"
                text="continue_with"
                width="336"
              />
            </div>
            {googleLoading && (
              <div style={{ textAlign: "center", marginTop: 8, fontSize: 13.5, color: "var(--gray-500)" }}>
                <span className="spinner" /> Signing you in with Google…
              </div>
            )}
          </>
        )}

        <div style={{ textAlign: "center", marginTop: 16, fontSize: 14.5 }}>
          <Link to="/forgot-password">Forgot password?</Link>
        </div>
        <div style={{ textAlign: "center", marginTop: 10, fontSize: 14.5 }}>
          New here? <Link to="/register">Create an account</Link>
        </div>
      </div>
    </div>
  );
}
