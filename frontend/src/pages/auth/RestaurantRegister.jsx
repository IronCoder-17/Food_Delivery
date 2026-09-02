import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { restaurantRegister } from "../../services/endpoints";
import StateCitySelect from "../../components/StateCitySelect";
import ThemeToggle from "../../components/ThemeToggle";

const emptyForm = {
  restaurant_name: "", owner_name: "", email: "", password: "", confirm_password: "",
  mobile_number: "", address: "", pincode: "", description: "",
  opening_time: "09:00", closing_time: "23:00",
};

export default function RestaurantRegister() {
  const [form, setForm] = useState(emptyForm);
  const [stateId, setStateId] = useState("");
  const [cityId, setCityId] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm_password) {
      setError("Password and confirm password do not match.");
      return;
    }
    if (!stateId || !cityId) {
      setError("Please select state and city.");
      return;
    }
    setLoading(true);
    try {
      await restaurantRegister({ ...form, state_id: stateId, city_id: cityId });
      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div style={{ maxWidth: 480, margin: "80px auto", padding: "0 20px" }}>
        <ThemeToggle variant="floating" />
        <div className="card" style={{ padding: 32, textAlign: "center" }}>
          <div style={{ fontSize: 40, marginBottom: 10 }}>✅</div>
          <h2>Application Submitted</h2>
          <p style={{ color: "var(--gray-500)" }}>
            Your restaurant application is <span className="badge badge-pending">Pending Approval</span>.
            An admin will review it shortly. You'll be able to log in once approved.
          </p>
          <button className="btn btn-primary" onClick={() => navigate("/restaurant/login")} style={{ marginTop: 12 }}>
            Go to Restaurant Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 620, margin: "40px auto", padding: "0 20px 60px" }}>
      <ThemeToggle variant="floating" />
      <div className="card" style={{ padding: 32 }}>
        <h2 style={{ textAlign: "center", color: "var(--orange)" }}>Restaurant Application</h2>
        <p style={{ textAlign: "center", color: "var(--gray-500)", marginBottom: 24 }}>
          Submit your details — an admin will review and approve your account.
        </p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="grid grid-2">
            <div className="field">
              <label>Restaurant Name</label>
              <input className="input" required value={form.restaurant_name} onChange={(e) => update("restaurant_name", e.target.value)} />
            </div>
            <div className="field">
              <label>Owner Name</label>
              <input className="input" required value={form.owner_name} onChange={(e) => update("owner_name", e.target.value)} />
            </div>
          </div>
          <div className="grid grid-2">
            <div className="field">
              <label>Restaurant Email</label>
              <input className="input" type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} />
            </div>
            <div className="field">
              <label>Mobile Number</label>
              <input className="input" required value={form.mobile_number} onChange={(e) => update("mobile_number", e.target.value.replace(/\D/g, "").slice(0, 10))} />
            </div>
          </div>
          <div className="grid grid-2">
            <div className="field">
              <label>Password</label>
              <input className="input" type="password" required value={form.password} onChange={(e) => update("password", e.target.value)} />
            </div>
            <div className="field">
              <label>Confirm Password</label>
              <input className="input" type="password" required value={form.confirm_password} onChange={(e) => update("confirm_password", e.target.value)} />
            </div>
          </div>

          <StateCitySelect stateId={stateId} cityId={cityId} onChange={({ stateId, cityId }) => { setStateId(stateId); setCityId(cityId); }} />

          <div className="field">
            <label>Restaurant Address</label>
            <textarea className="input" rows={2} required value={form.address} onChange={(e) => update("address", e.target.value)} />
          </div>
          <div className="field">
            <label>Pincode</label>
            <input className="input" required value={form.pincode} onChange={(e) => update("pincode", e.target.value.replace(/\D/g, "").slice(0, 6))} />
          </div>
          <div className="field">
            <label>Restaurant Description</label>
            <textarea className="input" rows={3} value={form.description} onChange={(e) => update("description", e.target.value)} />
          </div>
          <div className="grid grid-2">
            <div className="field">
              <label>Opening Time</label>
              <input className="input" type="time" value={form.opening_time} onChange={(e) => update("opening_time", e.target.value)} />
            </div>
            <div className="field">
              <label>Closing Time</label>
              <input className="input" type="time" value={form.closing_time} onChange={(e) => update("closing_time", e.target.value)} />
            </div>
          </div>

          <button className="btn btn-primary btn-block" disabled={loading} style={{ marginTop: 8 }}>
            {loading ? <span className="spinner" /> : "Submit Application"}
          </button>
        </form>
        <div style={{ textAlign: "center", marginTop: 16, fontSize: 14.5 }}>
          Already approved? <Link to="/restaurant/login">Log in</Link>
        </div>
      </div>
    </div>
  );
}
