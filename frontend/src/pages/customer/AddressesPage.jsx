import { useEffect, useState } from "react";
import {
  getAddresses, addAddress, updateAddress, deleteAddress, setDefaultAddress,
} from "../../services/endpoints";
import StateCitySelect from "../../components/StateCitySelect";

const LABELS = ["Home", "Work", "Hostel", "Other"];
const LABEL_ICON = { Home: "🏠", Work: "🏢", Hostel: "🏫", Other: "📍" };

const DELIVERY_INSTRUCTIONS = [
  { value: "ring_bell", label: "🔔 Ring Bell", hint: "Ring the doorbell" },
  { value: "silent_drop", label: "🤫 Silent Drop", hint: "Leave at door without ringing" },
  { value: "call_me", label: "📞 Call Me", hint: "Call customer on arrival" },
];
const DELIVERY_INSTRUCTION_LABEL = Object.fromEntries(DELIVERY_INSTRUCTIONS.map((d) => [d.value, d.label]));

const EMPTY_FORM = {
  label: "Home", contact_name: "", contact_phone: "", address: "",
  state_id: "", city_id: "", pincode: "", is_default: false, delivery_instruction: "ring_bell",
};

export default function AddressesPage() {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [editingId, setEditingId] = useState(null); // null = not editing, "new" = creating
  const [form, setForm] = useState(EMPTY_FORM);
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState(null);

  function load() {
    setLoading(true);
    setLoadError("");
    getAddresses()
      .then((res) => setAddresses(res.data))
      .catch((err) => setLoadError(err.message || "Failed to load addresses."))
      .finally(() => setLoading(false));
  }
  useEffect(() => { load(); }, []);

  function startNew() {
    setForm(EMPTY_FORM);
    setSaveError("");
    setEditingId("new");
  }

  function startEdit(addr) {
    setForm({
      label: addr.label || "Home",
      contact_name: addr.contact_name || "",
      contact_phone: addr.contact_phone || "",
      address: addr.address || "",
      state_id: addr.state_id || "",
      city_id: addr.city_id || "",
      pincode: addr.pincode || "",
      is_default: addr.is_default,
      delivery_instruction: addr.delivery_instruction || "ring_bell",
    });
    setSaveError("");
    setEditingId(addr.id);
  }

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaveError("");

    if (!form.address.trim()) {
      setSaveError("Address is required.");
      return;
    }
    if (form.pincode && !/^\d{6}$/.test(form.pincode)) {
      setSaveError("Pincode must be 6 digits.");
      return;
    }
    if (form.contact_phone && !/^[6-9]\d{9}$/.test(form.contact_phone)) {
      setSaveError("Enter a valid 10-digit contact phone, or leave it blank.");
      return;
    }

    setSaving(true);
    try {
      if (editingId === "new") {
        const res = await addAddress(form);
        setAddresses((prev) => [res.data, ...prev.map((a) => (form.is_default ? { ...a, is_default: false } : a))]);
      } else {
        const res = await updateAddress(editingId, form);
        setAddresses((prev) => prev.map((a) => (a.id === editingId ? res.data : (form.is_default ? { ...a, is_default: false } : a))));
      }
      setEditingId(null);
    } catch (err) {
      setSaveError(err.message || "Failed to save address.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this address?")) return;
    setBusyId(id);
    try {
      await deleteAddress(id);
      load(); // reload since deleting a default may promote another address
    } catch (err) {
      window.alert(err.message || "Failed to delete address.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleSetDefault(id) {
    setBusyId(id);
    try {
      await setDefaultAddress(id);
      setAddresses((prev) => prev.map((a) => ({ ...a, is_default: a.id === id })));
    } catch (err) {
      window.alert(err.message || "Failed to set default address.");
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return (
      <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 720 }}>
        <h2>Saved Addresses</h2>
        <div className="skeleton" style={{ height: 220, borderRadius: 12 }} />
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 720 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <h2 style={{ margin: 0 }}>Saved Addresses</h2>
        {editingId === null && <button className="btn btn-primary btn-sm" onClick={startNew}>+ Add Address</button>}
      </div>
      <p style={{ color: "var(--gray-500)", marginTop: 4 }}>
        Save multiple delivery addresses and pick one at checkout. Only one address can be the default at a time.
      </p>

      {loadError && <div className="alert alert-error">{loadError}</div>}

      {editingId !== null && (
        <form onSubmit={handleSave} className="card" style={{ padding: 20, marginBottom: 18 }}>
          <h4 style={{ marginTop: 0 }}>{editingId === "new" ? "Add New Address" : "Edit Address"}</h4>
          {saveError && <div className="alert alert-error">{saveError}</div>}

          <div className="field">
            <label>Label</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {LABELS.map((l) => (
                <button
                  type="button" key={l}
                  className={`btn btn-sm ${form.label === l ? "btn-primary" : "btn-outline"}`}
                  onClick={() => update("label", l)}
                >
                  {LABEL_ICON[l]} {l}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-2">
            <div className="field">
              <label>Contact Name (optional)</label>
              <input className="input" value={form.contact_name} onChange={(e) => update("contact_name", e.target.value)} />
            </div>
            <div className="field">
              <label>Contact Phone (optional)</label>
              <input className="input" value={form.contact_phone}
                onChange={(e) => update("contact_phone", e.target.value.replace(/\D/g, "").slice(0, 10))} />
            </div>
          </div>

          <div className="field">
            <label>Full Address</label>
            <textarea className="input" rows={2} required value={form.address} onChange={(e) => update("address", e.target.value)} />
          </div>

          <StateCitySelect
            stateId={form.state_id}
            cityId={form.city_id}
            onChange={({ stateId, cityId }) => setForm((f) => ({ ...f, state_id: stateId, city_id: cityId }))}
          />

          <div className="field">
            <label>Pincode</label>
            <input className="input" value={form.pincode}
              onChange={(e) => update("pincode", e.target.value.replace(/\D/g, "").slice(0, 6))} />
          </div>

          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14, marginBottom: 14 }}>
            <input type="checkbox" checked={form.is_default} onChange={(e) => update("is_default", e.target.checked)} />
            Set as default delivery address
          </label>

          <div className="field">
            <label>Delivery Instruction</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {DELIVERY_INSTRUCTIONS.map((d) => (
                <button
                  type="button" key={d.value}
                  className={`btn btn-sm ${form.delivery_instruction === d.value ? "btn-primary" : "btn-outline"}`}
                  onClick={() => update("delivery_instruction", d.value)}
                  title={d.hint}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-primary" disabled={saving}>{saving ? <span className="spinner" /> : "Save Address"}</button>
            <button type="button" className="btn btn-ghost" disabled={saving} onClick={() => setEditingId(null)}>Cancel</button>
          </div>
        </form>
      )}

      {addresses.length === 0 && editingId === null ? (
        <div className="empty-state">
          <div style={{ fontSize: 40 }}>📍</div>
          <h3>No saved addresses yet</h3>
          <p>Add a Home, Work, or other address for faster checkout.</p>
        </div>
      ) : (
        addresses.map((a) => (
          <div key={a.id} className="card" style={{ padding: 16, marginBottom: 12, display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontWeight: 700 }}>{LABEL_ICON[a.label] || "📍"} {a.label}</span>
                {a.is_default && <span className="badge badge-approved">Default</span>}
              </div>
              {a.contact_name && <div style={{ fontSize: 13.5, color: "var(--gray-700)", marginTop: 4 }}>{a.contact_name}{a.contact_phone ? ` · ${a.contact_phone}` : ""}</div>}
              <div style={{ fontSize: 14, marginTop: 4 }}>{a.address}</div>
              {a.pincode && <div style={{ fontSize: 13, color: "var(--gray-500)" }}>PIN {a.pincode}</div>}
              <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: 4 }}>
                {DELIVERY_INSTRUCTION_LABEL[a.delivery_instruction] || "🔔 Ring Bell"}
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
              {!a.is_default && (
                <button className="btn btn-outline btn-sm" disabled={busyId === a.id} onClick={() => handleSetDefault(a.id)}>
                  Set Default
                </button>
              )}
              <button className="btn btn-outline btn-sm" onClick={() => startEdit(a)}>Edit</button>
              <button className="btn btn-outline btn-sm" style={{ borderColor: "var(--red)", color: "var(--red)" }}
                disabled={busyId === a.id} onClick={() => handleDelete(a.id)}>
                {busyId === a.id ? "..." : "Delete"}
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
