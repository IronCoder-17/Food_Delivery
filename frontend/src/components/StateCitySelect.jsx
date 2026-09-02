import { useEffect, useState } from "react";
import { getStates, getCities } from "../services/endpoints";

export default function StateCitySelect({ stateId, cityId, onChange }) {
  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);
  const [loadingCities, setLoadingCities] = useState(false);

  useEffect(() => {
    getStates().then((res) => setStates(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!stateId) {
      setCities([]);
      return;
    }
    setLoadingCities(true);
    getCities(stateId)
      .then((res) => setCities(res.data))
      .finally(() => setLoadingCities(false));
  }, [stateId]);

  return (
    <div className="grid grid-2">
      <div className="field">
        <label>State</label>
        <select
          className="input"
          value={stateId || ""}
          onChange={(e) => onChange({ stateId: e.target.value ? Number(e.target.value) : "", cityId: "" })}
        >
          <option value="">Select State</option>
          {states.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>City</label>
        <select
          className="input"
          value={cityId || ""}
          onChange={(e) => onChange({ stateId, cityId: e.target.value ? Number(e.target.value) : "" })}
          disabled={!stateId || loadingCities}
        >
          <option value="">{loadingCities ? "Loading..." : "Select City"}</option>
          {cities.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
