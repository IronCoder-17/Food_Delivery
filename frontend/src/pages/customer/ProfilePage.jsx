import { useEffect, useState } from "react";
import { getCustomerProfile, updateCustomerProfile, getStates, getCities } from "../../services/endpoints";
import { useAuth } from "../../hooks/AuthContext";
import { useTheme } from "../../hooks/ThemeContext";
import StateCitySelect from "../../components/StateCitySelect";

const GENDER_OPTIONS = [
  { value: "", label: "Prefer not to say" },
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "other", label: "Other" },
];

const APPEARANCE_OPTIONS = [
  { value: "light", label: "☀️ Light", hint: "Always light" },
  { value: "dark", label: "🌙 Dark", hint: "Always dark" },
  { value: "system", label: "💻 System", hint: "Match your device's setting" },
  { value: "schedule", label: "🕗 Auto-schedule", hint: "Dark in the evening, light in the morning" },
];

const HOUR_LABELS = Array.from({ length: 24 }, (_, h) => {
  const period = h < 12 ? "AM" : "PM";
  const display = h % 12 === 0 ? 12 : h % 12;
  return `${display}:00 ${period}`;
});

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" });
}

export default function ProfilePage() {
  const { user } = useAuth();
  const { mode, scheduleHours, setMode, setScheduleHours } = useTheme();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(null);
  const [stateName, setStateName] = useState("");
  const [cityName, setCityName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");

  function loadProfile() {
    setLoading(true);
    setLoadError("");
    getCustomerProfile()
      .then((res) => setProfile(res.data))
      .catch((err) => setLoadError(err.message || "Failed to load profile."))
      .finally(() => setLoading(false));
  }

  // Always load from the server (not just cached login/localStorage state) so the
  // profile is correct after login, refresh, and logging back in.
  useEffect(() => { loadProfile(); }, []);

  // Resolve human-readable state/city names for display since the profile
  // record only stores state_id/city_id.
  useEffect(() => {
    if (!profile) return;
    getStates().then((res) => {
      const match = res.data.find((s) => s.id === profile.state_id);
      setStateName(match?.name || "");
    }).catch(() => {});
    if (profile.state_id) {
      getCities(profile.state_id).then((res) => {
        const match = res.data.find((c) => c.id === profile.city_id);
        setCityName(match?.name || "");
      }).catch(() => {});
    } else {
      setCityName("");
    }
  }, [profile]);

  function startEditing() {
    setForm({
      first_name: profile.first_name || "",
      last_name: profile.last_name || "",
      mobile_number: profile.mobile_number || "",
      date_of_birth: profile.date_of_birth || "",
      gender: profile.gender || "",
      address: profile.address || "",
      pincode: profile.pincode || "",
      state_id: profile.state_id || "",
      city_id: profile.city_id || "",
      profile_image_url: profile.profile_image_url || "",
    });
    setSaveError("");
    setSaveSuccess("");
    setEditing(true);
  }

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaveError("");
    setSaveSuccess("");

    if (!form.first_name.trim() || !form.last_name.trim()) {
      setSaveError("First name and last name are required.");
      return;
    }
    if (!/^[6-9]\d{9}$/.test(form.mobile_number)) {
      setSaveError("Enter a valid 10-digit Indian mobile number.");
      return;
    }
    if (form.pincode && !/^\d{6}$/.test(form.pincode)) {
      setSaveError("Pincode must be 6 digits.");
      return;
    }

    setSaving(true);
    try {
      const res = await updateCustomerProfile(form);
      setProfile(res.data.customer);
      setSaveSuccess(res.data.message || "Profile updated successfully.");
      setEditing(false);
    } catch (err) {
      setSaveError(err.message || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 640 }}>
        <h2>My Profile</h2>
        <div className="skeleton" style={{ height: 320, borderRadius: 12 }} />
      </div>
    );
  }

  if (loadError || !profile) {
    return (
      <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 640 }}>
        <h2>My Profile</h2>
        <div className="alert alert-error">{loadError || "Profile could not be loaded."}</div>
        <button className="btn btn-outline" onClick={loadProfile}>Retry</button>
      </div>
    );
  }

  const initials = `${profile.first_name?.[0] || user?.name?.[0] || "?"}`.toUpperCase();

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 640 }}>
      <h2>My Profile</h2>

      {saveSuccess && !editing && <div className="alert alert-success">{saveSuccess}</div>}

      <div className="card" style={{ padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 22 }}>
          {profile.profile_image_url ? (
            <img
              src={profile.profile_image_url}
              alt="Profile"
              style={{ width: 64, height: 64, borderRadius: "50%", objectFit: "cover" }}
              onError={(e) => { e.target.style.display = "none"; }}
            />
          ) : (
            <div style={{ width: 64, height: 64, borderRadius: "50%", background: "var(--orange)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, fontWeight: 700 }}>
              {initials}
            </div>
          )}
          <div>
            <div style={{ fontWeight: 700, fontSize: 19 }}>{profile.first_name} {profile.last_name}</div>
            <div style={{ color: "var(--gray-500)" }}>{profile.email}</div>
          </div>
          {!editing && (
            <button className="btn btn-outline btn-sm" style={{ marginLeft: "auto" }} onClick={startEditing}>
              Edit Profile
            </button>
          )}
        </div>

        {!editing ? (
          <div className="grid grid-2" style={{ rowGap: 16 }}>
            <ProfileField label="Email" value={profile.email} />
            <ProfileField label="Mobile Number" value={profile.mobile_number} extra={profile.mobile_verified ? " (verified)" : " (unverified)"} />
            <ProfileField label="Date of Birth" value={profile.date_of_birth ? formatDate(profile.date_of_birth) : "Not provided"} />
            <ProfileField label="Gender" value={GENDER_OPTIONS.find((g) => g.value === profile.gender)?.label || "Not provided"} />
            <ProfileField label="State" value={stateName || "Not set"} />
            <ProfileField label="City" value={cityName || "Not set"} />
            <ProfileField label="Pincode" value={profile.pincode || "Not provided"} />
            <ProfileField label="Member Since" value={profile.created_at ? formatDate(profile.created_at) : "—"} />
            <div style={{ gridColumn: "1 / -1" }}>
              <ProfileField label="Address" value={profile.address || "Not provided"} />
            </div>
          </div>
        ) : (
          <form onSubmit={handleSave}>
            {saveError && <div className="alert alert-error">{saveError}</div>}

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
              <input className="input" value={profile.email} disabled />
              <div className="hint">Email cannot be changed here.</div>
            </div>

            <div className="field">
              <label>Mobile Number</label>
              <input className="input" required value={form.mobile_number}
                onChange={(e) => update("mobile_number", e.target.value.replace(/\D/g, "").slice(0, 10))} />
            </div>

            <div className="grid grid-2">
              <div className="field">
                <label>Date of Birth</label>
                <input className="input" type="date" value={form.date_of_birth} onChange={(e) => update("date_of_birth", e.target.value)} />
              </div>
              <div className="field">
                <label>Gender</label>
                <select className="input" value={form.gender} onChange={(e) => update("gender", e.target.value)}>
                  {GENDER_OPTIONS.map((g) => (
                    <option key={g.value} value={g.value}>{g.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <StateCitySelect
              stateId={form.state_id}
              cityId={form.city_id}
              onChange={({ stateId, cityId }) => setForm((f) => ({ ...f, state_id: stateId, city_id: cityId }))}
            />

            <div className="field">
              <label>Address</label>
              <textarea className="input" rows={2} value={form.address} onChange={(e) => update("address", e.target.value)} />
            </div>

            <div className="field">
              <label>Pincode</label>
              <input className="input" value={form.pincode}
                onChange={(e) => update("pincode", e.target.value.replace(/\D/g, "").slice(0, 6))} />
            </div>

            <div className="field">
              <label>Profile Photo URL</label>
              <input className="input" value={form.profile_image_url} placeholder="https://..."
                onChange={(e) => update("profile_image_url", e.target.value)} />
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
              <button className="btn btn-primary" disabled={saving}>
                {saving ? <span className="spinner" /> : "Save Changes"}
              </button>
              <button type="button" className="btn btn-ghost" disabled={saving} onClick={() => setEditing(false)}>
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      <div className="card" style={{ padding: 24, marginTop: 20 }}>
        <h3 style={{ marginBottom: 4 }}>Appearance</h3>
        <p style={{ color: "var(--gray-500)", fontSize: 13.5, marginBottom: 16 }}>
          Choose how the app looks. This only affects the customer pages on this device.
        </p>

        <div style={{ display: "grid", gap: 10, gridTemplateColumns: "1fr 1fr" }}>
          {APPEARANCE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className="card"
              onClick={() => setMode(opt.value)}
              style={{
                textAlign: "left", padding: 14, cursor: "pointer",
                border: mode === opt.value ? "2px solid var(--orange)" : "1px solid var(--gray-100)",
                background: mode === opt.value ? "var(--orange-light)" : "var(--card-bg)",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: 14.5 }}>{opt.label}</div>
              <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: 2 }}>{opt.hint}</div>
            </button>
          ))}
        </div>

        {mode === "schedule" && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 20, marginTop: 18, paddingTop: 16, borderTop: "1px solid var(--gray-100)" }}>
            <div className="field" style={{ marginBottom: 0, minWidth: 180 }}>
              <label>Switch to dark at</label>
              <select className="input" value={scheduleHours.start}
                onChange={(e) => setScheduleHours({ ...scheduleHours, start: Number(e.target.value) })}>
                {HOUR_LABELS.map((label, h) => <option key={h} value={h}>{label}</option>)}
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0, minWidth: 180 }}>
              <label>Switch to light at</label>
              <select className="input" value={scheduleHours.end}
                onChange={(e) => setScheduleHours({ ...scheduleHours, end: Number(e.target.value) })}>
                {HOUR_LABELS.map((label, h) => <option key={h} value={h}>{label}</option>)}
              </select>
            </div>
          </div>
        )}

        <p style={{ color: "var(--gray-500)", fontSize: 12, marginTop: 16, marginBottom: 0 }}>
          Tip: press <strong>Ctrl/Cmd + Shift + L</strong> anywhere to quickly flip between light and dark.
        </p>
      </div>
    </div>
  );
}

function ProfileField({ label, value, extra }) {
  return (
    <div>
      <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", letterSpacing: 0.3, marginBottom: 3 }}>
        {label}
      </div>
      <div style={{ fontSize: 15 }}>{value}{extra}</div>
    </div>
  );
}
