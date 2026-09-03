import { useEffect, useState } from "react";
import { adminListQuestions, adminAddQuestion, adminUpdateQuestion, adminDeleteQuestion, adminGameStats } from "../../services/endpoints";
import StatCard from "../../components/StatCard";

const emptyForm = { question: "", option_a: "", option_b: "", option_c: "", option_d: "", correct_option: "A" };

export default function AdminGameQuestions() {
  const [questions, setQuestions] = useState([]);
  const [stats, setStats] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    Promise.all([adminListQuestions(), adminGameStats()])
      .then(([q, s]) => { setQuestions(q.data); setStats(s.data); })
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  function openAdd() { setForm(emptyForm); setEditingId(null); setShowForm(true); setError(""); }
  function openEdit(q) { setForm(q); setEditingId(q.id); setShowForm(true); setError(""); }

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    try {
      if (editingId) await adminUpdateQuestion(editingId, form);
      else await adminAddQuestion(form);
      setShowForm(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function toggleActive(q) {
    await adminUpdateQuestion(q.id, { is_active: !q.is_active });
    load();
  }

  async function handleDelete(q) {
    if (!confirm("Delete this question?")) return;
    await adminDeleteQuestion(q.id);
    load();
  }

  return (
    <div>
      <h2>GK Question Bank</h2>

      {stats && (
        <div className="grid grid-3" style={{ marginBottom: 20 }}>
          <StatCard label="Sessions Played" value={stats.total_sessions_played} />
          <StatCard label="Total Rewards Paid" value={`₹${stats.total_rewards_paid}`} accent />
          <StatCard label="Average Score" value={stats.average_score} />
        </div>
      )}

      <button className="btn btn-primary" onClick={openAdd} style={{ marginBottom: 16 }}>+ Add Question</button>

      {showForm && (
        <div className="card" style={{ padding: 22, marginBottom: 20 }}>
          <h4>{editingId ? "Edit Question" : "New Question"}</h4>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleSave}>
            <div className="field"><label>Question</label><textarea className="input" rows={2} required value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })} /></div>
            <div className="grid grid-2">
              <div className="field"><label>Option A</label><input className="input" required value={form.option_a} onChange={(e) => setForm({ ...form, option_a: e.target.value })} /></div>
              <div className="field"><label>Option B</label><input className="input" required value={form.option_b} onChange={(e) => setForm({ ...form, option_b: e.target.value })} /></div>
              <div className="field"><label>Option C</label><input className="input" required value={form.option_c} onChange={(e) => setForm({ ...form, option_c: e.target.value })} /></div>
              <div className="field"><label>Option D</label><input className="input" required value={form.option_d} onChange={(e) => setForm({ ...form, option_d: e.target.value })} /></div>
            </div>
            <div className="field">
              <label>Correct Answer</label>
              <select className="input" value={form.correct_option} onChange={(e) => setForm({ ...form, correct_option: e.target.value })}>
                <option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-primary">{editingId ? "Save Changes" : "Add Question"}</button>
              <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {loading ? <div className="skeleton" style={{ height: 300 }} /> : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          {questions.map((q, idx) => (
            <div key={q.id} style={{ padding: 14, borderBottom: idx < questions.length - 1 ? "1px solid var(--gray-100)" : "none" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <div style={{ flex: 1 }}>
                  <strong>{q.question}</strong>
                  <div style={{ fontSize: 13.5, color: "var(--gray-500)", marginTop: 4 }}>
                    A: {q.option_a} · B: {q.option_b} · C: {q.option_c} · D: {q.option_d} — <strong>Correct: {q.correct_option}</strong>
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end" }}>
                  <button className={`badge ${q.is_active ? "badge-approved" : "badge-rejected"}`} style={{ border: "none", cursor: "pointer" }} onClick={() => toggleActive(q)}>
                    {q.is_active ? "Active" : "Inactive"}
                  </button>
                  <div>
                    <button className="btn btn-sm btn-ghost" onClick={() => openEdit(q)}>Edit</button>
                    <button className="btn btn-sm btn-ghost" style={{ color: "var(--red)" }} onClick={() => handleDelete(q)}>Delete</button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
