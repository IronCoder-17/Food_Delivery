import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { sendOtp, verifyOtp, customerRegister } from "../../services/endpoints";
import { useAuth } from "../../hooks/AuthContext";
import StateCitySelect from "../../components/StateCitySelect";

const emptyForm = {
  first_name: "", last_name: "", email: "", password: "", confirm_password: "",
  mobile_number: "", address: "", pincode: "", referral_code: "",
};

export default function CustomerRegister() {
  const [form, setForm] = useState(emptyForm);
  const [stateId, setStateId] = useState("");
  const [cityId, setCityId] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSendOtp() {
    setError(""); setInfo("");
    if (!/^[6-9]\d{9}$/.test(form.mobile_number)) {
      setError("Enter a valid 10-digit Indian mobile number.");
      return;
    }
    setLoading(true);
    try {
      const res = await sendOtp(form.mobile_number);
      setOtpSent(true);
      if (res.data.dev_otp) {
        setDevOtp(res.data.dev_otp);
        setInfo(`OTP sent. (Dev mode — no SMS gateway configured, your test code is ${res.data.dev_otp})`);
      } else {
        setInfo("OTP sent to your mobile number.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp() {
    setError(""); setInfo("");
    setLoading(true);
    try {
      await verifyOtp(form.mobile_number, otpCode);
      setOtpVerified(true);
      setInfo("Mobile number verified successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!otpVerified) {
      setError("Please verify your mobile number with OTP before continuing.");
      return;
    }
    if (form.password !== form.confirm_password) {
      setError("Password and confirm password do not match.");
      return;
    }
    if (!stateId || !cityId) {
      setError("Please select your state and city.");
      return;
    }
    setLoading(true);
    try {
      const res = await customerRegister({ ...form, state_id: stateId, city_id: cityId });
      login(res.data.token, res.data.user);
      if (res.data.referral_warning) {
        // Registration itself succeeded; only the referral link didn't apply.
        window.alert(res.data.referral_warning);
      }
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 560, margin: "40px auto", padding: "0 20px 60px" }}>
      <div className="card" style={{ padding: 32 }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Create Customer Account</h2>
        <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 24 }}>Join QuickBite and start ordering.</p>

        {error && <div className="alert alert-error">{error}</div>}
        {info && <div className="alert alert-info">{info}</div>}

        <form onSubmit={handleSubmit}>
          <div className="grid grid-2">
            <div className="field">
              <label>First Name</label>
              <input className="input" required value={form.first_name} onChange={(e) => update("first_name", e.target.value)} />
            </div>
            <div className="field">
              <label>Last Name</label>
              <input className="input" required value={form.last_name} onChange={(e) => update("last_name", e.target.value)} />
            </div>
          </div>

          <div className="field">
            <label>Email Address</label>
            <input className="input" type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} />
          </div>

          <div className="grid grid-2">
            <div className="field">
              <label>Password</label>
              <input className="input" type="password" required value={form.password} onChange={(e) => update("password", e.target.value)} />
              <div className="hint">Min 8 chars, 1 uppercase, 1 lowercase, 1 number.</div>
            </div>
            <div className="field">
              <label>Confirm Password</label>
              <input className="input" type="password" required value={form.confirm_password} onChange={(e) => update("confirm_password", e.target.value)} />
            </div>
          </div>

          <div className="field">
            <label>Mobile Number</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input className="input" required value={form.mobile_number} disabled={otpVerified}
                onChange={(e) => update("mobile_number", e.target.value.replace(/\D/g, "").slice(0, 10))}
                placeholder="10-digit mobile number" />
              <button type="button" className="btn btn-outline" disabled={loading || otpVerified} onClick={handleSendOtp}>
                {otpSent ? "Resend OTP" : "Send OTP"}
              </button>
            </div>
          </div>

          {otpSent && !otpVerified && (
            <div className="field">
              <label>Enter OTP</label>
              <div style={{ display: "flex", gap: 8 }}>
                <input className="input" value={otpCode} onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="6-digit OTP" />
                <button type="button" className="btn btn-primary" disabled={loading} onClick={handleVerifyOtp}>Verify OTP</button>
              </div>
            </div>
          )}
          {otpVerified && <div className="badge badge-approved" style={{ marginBottom: 14 }}>✓ Mobile Verified</div>}

          <StateCitySelect stateId={stateId} cityId={cityId} onChange={({ stateId, cityId }) => { setStateId(stateId); setCityId(cityId); }} />

          <div className="field">
            <label>Complete Delivery Address</label>
            <textarea className="input" rows={2} required value={form.address} onChange={(e) => update("address", e.target.value)} />
          </div>

          <div className="field">
            <label>Pincode</label>
            <input className="input" required value={form.pincode} onChange={(e) => update("pincode", e.target.value.replace(/\D/g, "").slice(0, 6))} />
          </div>

          <div className="field">
            <label>Referral Code (optional)</label>
            <input className="input" placeholder="QB-XXXXX-1234" value={form.referral_code}
              onChange={(e) => update("referral_code", e.target.value.toUpperCase())} />
          </div>

          <button className="btn btn-primary btn-block" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : "Create Account"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 16, fontSize: 14.5 }}>
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  );
}
