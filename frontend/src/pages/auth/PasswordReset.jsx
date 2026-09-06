import { useState } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { forgotPassword, resetPassword } from "../../services/endpoints";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      setMessage(
        res.data.message ||
          "If that email is registered, a password reset link has been sent. Please check your inbox and spam folder."
      );
      setSubmitted(true);
    } catch (err) {
      // Never surface internal SMTP/server details -- just a safe, generic
      // message. The interceptor in services/api.js already strips these
      // down to err.message, so this is customer-facing by construction.
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "60px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 32 }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Forgot Password</h2>
        {message && <div className="alert alert-success">{message}</div>}
        {error && <div className="alert alert-error">{error}</div>}
        {!submitted && (
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label>Email Address</label>
              <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-block" disabled={loading}>
              {loading ? <span className="spinner" /> : "Send Reset Link"}
            </button>
          </form>
        )}
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
        {success && <div className="alert alert-success">Password reset successful. Redirecting to login...</div>}
        {!token && !success && (
          <div className="alert alert-error">
            This reset link is missing its token. Please use the link from your email, or request a new one.
          </div>
        )}
        {!success && (
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label>New Password</label>
              <input className="input" type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </div>
            <div className="field">
              <label>Confirm New Password</label>
              <input className="input" type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-block" disabled={loading || !token}>
              {loading ? <span className="spinner" /> : "Reset Password"}
            </button>
          </form>
        )}
        {!success && (
          <div style={{ textAlign: "center", marginTop: 16 }}><Link to="/forgot-password">Request a new link</Link></div>
        )}
      </div>
    </div>
  );
}
