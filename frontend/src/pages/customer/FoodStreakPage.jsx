import { useEffect, useState } from "react";
import { getFoodStreak } from "../../services/endpoints";

export default function FoodStreakPage() {
  const [streak, setStreak] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getFoodStreak()
      .then((res) => setStreak(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="spinner" />;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 60, maxWidth: 700 }}>
      <h2 style={{ marginTop: 0 }}>🔥 Food Streak</h2>
      <p style={{ color: "var(--gray-500)", fontSize: 14 }}>
        Log in, order, or play the GK Game on consecutive days to build your streak. Just staying
        engaged earns rewards -- you don't need to order every day.
      </p>

      <div className="card" style={{ padding: 24, textAlign: "center" }}>
        <div style={{ fontSize: 40, fontWeight: 800, color: "var(--orange)" }}>🔥 {streak.current_streak}</div>
        <div style={{ fontSize: 13.5, color: "var(--gray-500)", marginBottom: 20 }}>day streak</div>

        <div style={{ display: "flex", justifyContent: "space-around", borderTop: "1px solid var(--gray-100)", paddingTop: 16 }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>🏆 {streak.best_streak}</div>
            <div style={{ fontSize: 12, color: "var(--gray-500)" }}>Best Streak</div>
          </div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>⭐ {streak.streak_points}</div>
            <div style={{ fontSize: 12, color: "var(--gray-500)" }}>Streak Points</div>
          </div>
        </div>

        <p style={{ fontSize: 12.5, color: "var(--gray-500)", marginTop: 18 }}>
          {streak.days_to_next_milestone} more day{streak.days_to_next_milestone === 1 ? "" : "s"} to your next milestone reward.
        </p>
      </div>
    </div>
  );
}