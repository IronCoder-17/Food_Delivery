import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { sendOtp, verifyOtp, completeGoogleProfile } from "../../services/endpoints";
import { useAuth } from "../../hooks/AuthContext";
import { tokenKey } from "../../utils/authScope";
import StateCitySelect from "../../components/StateCitySelect";

// Shown right after a brand-new Google sign-in. Google verifies email, but
// this app still needs a verified mobile number plus address/state/city/
// pincode before the account can be treated as complete -- we never invent
// any of these values.
export default function CompleteProfile() {
  const { user, login } = useAuth();
  const [mobile, setMobile] = useState("");
  const [stateId, setStateId] = useState("");
  const [cityId, setCityId] = useState("");
  const [address, setAddress] = useState("");
  const [pincode, setPincode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Already complete (e.g. a returning Google customer navigating here
    // directly, or hitting back after finishing) -- nothing to do here.
    if (user && !user.needs_profile_completion) {
      navigate("/", { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  async function handleSendOtp() {
    setError(""); setInfo("");
    if (!/^[6-9]\d{9}$/.test(mobile)) {
      setError("Enter a valid 10-digit Indian mobile number.");
      return;
    }
    setLoading(true);
    try {
      const res = await sendOtp(mobile);
      setOtpSent(true);
      if (res.data.dev_otp) {
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
      await verifyOtp(mobile, otpCode);
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
    if (!stateId || !cityId) {
      setError("Please select your state and city.");
      return;
    }
    setLoading(true);
    try {
      const res = await completeGoogleProfile({
        mobile_number: mobile,
        state_id: stateId,
        city_id: cityId,
        address,
        pincode,
      });
      // Refresh the stored session with the now-complete customer, so
      // ProtectedRoute stops redirecting here on every page.
      const existingToken = localStorage.getItem(tokenKey("customer"));
      login(existingToken, {
        ...user,
        name: `${res.data.customer.first_name} ${res.data.customer.last_name}`.trim(),
        profile_completed: true,
        needs_profile_completion: false,
      });
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
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Complete Your Profile</h2>
        <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 24 }}>
          Just a few more details to finish setting up your account.
        </p>

        {error && <div className="alert alert-error">{error}</div>}
        {info && <div className="alert alert-info">{info}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Mobile Number</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                className="input"
                required
                value={mobile}
                disabled={otpVerified}
                onChange={(e) => setMobile(e.target.value.replace(/\D/g, "").slice(0, 10))}
                placeholder="10-digit mobile number"
              />
              <button type="button" className="btn btn-outline" disabled={loading || otpVerified} onClick={handleSendOtp}>
                {otpSent ? "Resend OTP" : "Send OTP"}
              </button>
            </div>
          </div>

          {otpSent && !otpVerified && (
            <div className="field">
              <label>Enter OTP</label>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  className="input"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="6-digit OTP"
                />
                <button type="button" className="btn btn-primary" disabled={loading} onClick={handleVerifyOtp}>Verify OTP</button>
              </div>
            </div>
          )}
          {otpVerified && <div className="badge badge-approved" style={{ marginBottom: 14 }}>✓ Mobile Verified</div>}

          <StateCitySelect
            stateId={stateId}
            cityId={cityId}
            onChange={({ stateId, cityId }) => { setStateId(stateId); setCityId(cityId); }}
          />

          <div className="field">
            <label>Complete Delivery Address</label>
            <textarea className="input" rows={2} required value={address} onChange={(e) => setAddress(e.target.value)} />
          </div>

          <div className="field">
            <label>Pincode</label>
            <input
              className="input"
              required
              value={pincode}
              onChange={(e) => setPincode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            />
          </div>

          <button className="btn btn-primary btn-block" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : "Finish Setting Up My Account"}
          </button>
        </form>
      </div>
    </div>
  );
}
