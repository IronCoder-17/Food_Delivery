import { useEffect, useState } from "react";
import { getRestaurantProfile, updateRestaurantProfile } from "../../services/endpoints";
import StateCitySelect from "../../components/StateCitySelect";

const emptyForm = {
  restaurant_name: "", owner_name: "", mobile_number: "", address: "", pincode: "",
  description: "", opening_time: "", closing_time: "", logo_url: "", cover_image_url: "",
};

export default function RestaurantProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [form, setForm] = useState(emptyForm);
  const [stateId, setStateId] = useState("");
  const [cityId, setCityId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function loadProfile() {
    setLoading(true);
    setLoadError("");
    getRestaurantProfile()
      .then((res) => {
        const d = res.data;
        setProfile(d);
        setForm({
          restaurant_name: d.restaurant_name || "", owner_name: d.owner_name || "",
          mobile_number: d.mobile_number || "", address: d.address || "", pincode: d.pincode || "",
          description: d.description || "", opening_time: d.opening_time || "", closing_time: d.closing_time || "",
          logo_url: d.logo_url || "", cover_image_url: d.cover_image_url || "",
        });
        setStateId(d.state_id || "");
        setCityId(d.city_id || "");
      })
      .catch((err) => setLoadError(err.message || "Failed to load restaurant profile."))
      .finally(() => setLoading(false));
  }

  // Loaded from the server on every mount (not just kept in memory), so the
  // profile stays correct after login, refresh, and logging back in.
  useEffect(() => { loadProfile(); }, []);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    if (!form.restaurant_name.trim() || !form.owner_name.trim()) {
      setError("Restaurant name and owner name are required.");
      return;
    }
    if (!/^[6-9]\d{9}$/.test(form.mobile_number)) {
      setError("Enter a valid 10-digit Indian mobile number.");
      return;
    }
    if (form.pincode && !/^\d{6}$/.test(form.pincode)) {
      setError("Pincode must be 6 digits.");
      return;
    }

    setSaving(true);
    try {
      const res = await updateRestaurantProfile({ ...form, state_id: stateId, city_id: cityId });
      setProfile(res.data.restaurant);
      setMessage(res.data.message || "Profile updated successfully.");
    } catch (err) {
      setError(err.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="skeleton" style={{ height: 420, maxWidth: 640, borderRadius: 12 }} />;

  if (loadError || !profile) {
    return (
      <div style={{ maxWidth: 640 }}>
        <h2>Restaurant Profile</h2>
        <div className="alert alert-error">{loadError || "Profile could not be loaded."}</div>
        <button className="btn btn-outline" onClick={loadProfile}>Retry</button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h2>Restaurant Profile</h2>
      <div className="card" style={{ padding: 22 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
          {profile.logo_url ? (
            <img src={profile.logo_url} alt="Logo" style={{ width: 56, height: 56, borderRadius: 10, objectFit: "cover" }}
              onError={(e) => { e.target.style.display = "none"; }} />
          ) : (
            <div style={{ width: 56, height: 56, borderRadius: 10, background: "var(--orange)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, fontWeight: 700 }}>
              {profile.restaurant_name?.[0]?.toUpperCase() || "R"}
            </div>
          )}
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>{profile.restaurant_name}</div>
            <div style={{ color: "var(--gray-500)", fontSize: 14 }}>{profile.email}</div>
          </div>
          <div style={{ marginLeft: "auto", textAlign: "right" }}>
            <span className={`badge badge-${profile.status === "approved" ? "approved" : profile.status === "pending" ? "pending" : "rejected"}`}>
              {profile.status}
            </span>
            {profile.rating > 0 && (
              <div style={{ marginTop: 6, fontSize: 14, color: "var(--gray-700)" }}>★ {profile.rating.toFixed(1)}</div>
            )}
          </div>
        </div>

        {message && <div className="alert alert-success">{message}</div>}
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSave}>
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
              <label>Email</label>
              <input className="input" value={profile.email} disabled />
              <div className="hint">Email cannot be changed here.</div>
            </div>
            <div className="field">
              <label>Mobile Number</label>
              <input className="input" required value={form.mobile_number}
                onChange={(e) => update("mobile_number", e.target.value.replace(/\D/g, "").slice(0, 10))} />
            </div>
          </div>

          <StateCitySelect stateId={stateId} cityId={cityId} onChange={({ stateId, cityId }) => { setStateId(stateId); setCityId(cityId); }} />

          <div className="field">
            <label>Address</label>
            <textarea className="input" rows={2} value={form.address} onChange={(e) => update("address", e.target.value)} />
          </div>

          <div className="field">
            <label>Pincode</label>
            <input className="input" value={form.pincode}
              onChange={(e) => update("pincode", e.target.value.replace(/\D/g, "").slice(0, 6))} />
          </div>

          <div className="grid grid-2">
            <div className="field">
              <label>Opening Time</label>
              <input className="input" type="time" value={form.opening_time || ""} onChange={(e) => update("opening_time", e.target.value)} />
            </div>
            <div className="field">
              <label>Closing Time</label>
              <input className="input" type="time" value={form.closing_time || ""} onChange={(e) => update("closing_time", e.target.value)} />
            </div>
          </div>

          <div className="field">
            <label>Description</label>
            <textarea className="input" rows={3} value={form.description || ""} onChange={(e) => update("description", e.target.value)} />
          </div>

          <div className="grid grid-2">
            <div className="field">
              <label>Logo URL</label>
              <input className="input" placeholder="https://..." value={form.logo_url} onChange={(e) => update("logo_url", e.target.value)} />
            </div>
            <div className="field">
              <label>Cover Image URL</label>
              <input className="input" placeholder="https://..." value={form.cover_image_url} onChange={(e) => update("cover_image_url", e.target.value)} />
            </div>
          </div>

          <button className="btn btn-primary" disabled={saving}>
            {saving ? <span className="spinner" /> : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
