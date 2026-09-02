import { useState } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { forgotPassword, resetPassword } from "../../services/endpoints";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [devToken, setDevToken] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      setMessage(res.data.message);
      if (res.data.dev_reset_token) setDevToken(res.data.dev_reset_token);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 32 }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Forgot Password</h2>
        {message && <div className="alert alert-success">{message}</div>}
        {devToken && (
          <div className="alert alert-info">
            Dev mode (no email service configured) —{" "}
            <Link to={`/reset-password?token=${devToken}`}>click here to reset your password</Link>.
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email Address</label>
            <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? <span className="spinner" /> : "Send Reset Link"}
          </button>
        </form>
        <div style={{ textAlign: "center", marginTop: 16 }}><Link to="/login">Back to login</Link></div>
      </div>
    </div>
  );
}

export function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await resetPassword({ token, new_password: newPassword, confirm_password: confirmPassword });
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 32 }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Reset Password</h2>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">Password reset! Redirecting to login…</div>}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>New Password</label>
            <input className="input" type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div className="field">
            <label>Confirm New Password</label>
            <input className="input" type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? <span className="spinner" /> : "Reset Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
