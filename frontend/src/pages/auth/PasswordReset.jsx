import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { forgotPassword, verifyEmailOtp, resendEmailOtp, resetPassword } from "../../services/endpoints";

const RESEND_COOLDOWN_SECONDS = 30;
const STEP_EMAIL = 1;
const STEP_OTP = 2;
const STEP_NEW_PASSWORD = 3;
const STEP_DONE = 4;

export function ForgotPassword() {
  const [step, setStep] = useState(STEP_EMAIL);
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setInterval(() => setResendCooldown((s) => Math.max(s - 1, 0)), 1000);
    return () => clearInterval(t);
  }, [resendCooldown]);

  async function handleSendOtp(e) {
    e.preventDefault();
    setError(""); setInfo("");
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      setInfo(res.data.message || "If an account exists with this email, an OTP has been sent.");
      setResendCooldown(RESEND_COOLDOWN_SECONDS);
      setStep(STEP_OTP);
    } catch (err) {
      // Never surface internal SMTP/server details -- just a safe, generic
      // message. The interceptor in services/api.js already strips these
      // down to err.message, so this is customer-facing by construction.
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResendOtp() {
    if (resendCooldown > 0) return;
    setError(""); setInfo("");
    setLoading(true);
    try {
      const res = await resendEmailOtp(email, "FORGOT_PASSWORD");
      setInfo(res.data.message || "OTP resent. Please check your inbox and spam folder.");
      setResendCooldown(RESEND_COOLDOWN_SECONDS);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(e) {
    e.preventDefault();
    setError(""); setInfo("");
    setLoading(true);
    try {
      const res = await verifyEmailOtp(email, otp, "FORGOT_PASSWORD");
      // The backend only hands out this short-lived authorization after it
      // verifies the OTP itself -- the frontend never asserts "verified" on
      // its own, and /reset-password re-checks this token server-side too.
      setResetToken(res.data.reset_token);
      setStep(STEP_NEW_PASSWORD);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleResetPassword(e) {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await resetPassword({ token: resetToken, new_password: newPassword, confirm_password: confirmPassword });
      setStep(STEP_DONE);
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
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Forgot Password</h2>

        {error && <div className="alert alert-error">{error}</div>}
        {info && <div className="alert alert-info">{info}</div>}

        {step === STEP_EMAIL && (
          <form onSubmit={handleSendOtp}>
            <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 20 }}>
              Enter your registered email address.
            </p>
            <div className="field">
              <label>Email Address</label>
              <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value.trim())} />
            </div>
            <button className="btn btn-primary btn-block" disabled={loading}>
              {loading ? <span className="spinner" /> : "Send OTP"}
            </button>
          </form>
        )}

        {step === STEP_OTP && (
          <form onSubmit={handleVerifyOtp}>
            <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 20 }}>
              OTP sent to your email. Please check your inbox and spam folder.
            </p>
            <div className="field">
              <label>Enter OTP</label>
              <input className="input" required value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="6-digit OTP" inputMode="numeric" style={{ textAlign: "center", letterSpacing: 6, fontSize: 20 }} />
            </div>
            <button className="btn btn-primary btn-block" disabled={loading || otp.length !== 6}>
              {loading ? <span className="spinner" /> : "Verify OTP"}
            </button>
            <div style={{ textAlign: "center", marginTop: 14 }}>
              {resendCooldown > 0 ? (
                <span className="hint">Resend OTP in {resendCooldown}s</span>
              ) : (
                <button type="button" className="btn btn-outline" style={{ padding: "4px 12px", fontSize: 13 }}
                  disabled={loading} onClick={handleResendOtp}>
                  Resend OTP
                </button>
              )}
            </div>
          </form>
        )}

        {step === STEP_NEW_PASSWORD && (
          <form onSubmit={handleResetPassword}>
            <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 20 }}>Create your new password.</p>
            <div className="field">
              <label>New Password</label>
              <input className="input" type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              <div className="hint">Min 8 chars, 1 uppercase, 1 lowercase, 1 number.</div>
            </div>
            <div className="field">
              <label>Confirm Password</label>
              <input className="input" type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-block" disabled={loading}>
              {loading ? <span className="spinner" /> : "Reset Password"}
            </button>
          </form>
        )}

        {step === STEP_DONE && (
          <div className="alert alert-success">Password reset successful. Redirecting to login...</div>
        )}

        {step !== STEP_DONE && (
          <div style={{ textAlign: "center", marginTop: 16 }}><Link to="/login">Back to login</Link></div>
        )}
      </div>
    </div>
  );
}

// Kept only so any old bookmarked /reset-password?token=... link still
// lands somewhere sane -- the flow now always starts at /forgot-password
// (email -> OTP -> new password), so this just redirects there.
export function ResetPassword() {
  const navigate = useNavigate();
  useEffect(() => {
    navigate("/forgot-password", { replace: true });
  }, [navigate]);
  return null;
}
