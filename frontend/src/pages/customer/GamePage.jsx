import { useEffect, useRef, useState, useCallback } from "react";
import { startGame, submitAnswer, finishGame } from "../../services/endpoints";
import { useCart } from "../../hooks/CartContext";

const TIME_LIMIT = 10;

export default function GamePage() {
  const [phase, setPhase] = useState("intro"); // intro | playing | result
  const [sessionId, setSessionId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [qIndex, setQIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState(TIME_LIMIT);
  const [selected, setSelected] = useState(null);
  const [feedback, setFeedback] = useState(null); // {correct, correct_option}
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);
  const questionStartRef = useRef(null);

  const currentQuestion = questions[qIndex];

  const clearTimer = () => { if (timerRef.current) clearInterval(timerRef.current); };

  const goToNextOrFinish = useCallback(async (finalSessionId, finalQuestions, nextIndex) => {
    if (nextIndex >= finalQuestions.length) {
      try {
        const res = await finishGame(finalSessionId);
        setResult(res.data);
        setPhase("result");
      } catch (err) {
        setError(err.message);
      }
      return;
    }
    setQIndex(nextIndex);
    setSelected(null);
    setFeedback(null);
    setTimeLeft(TIME_LIMIT);
    questionStartRef.current = Date.now();
  }, []);

  const handleAnswer = useCallback(async (option, sid = sessionId, qs = questions, idx = qIndex) => {
    if (feedback) return; // already answered this question
    clearTimer();
    const question = qs[idx];
    const elapsed = (Date.now() - questionStartRef.current) / 1000;
    setSelected(option);
    try {
      const res = await submitAnswer({
        session_id: sid,
        question_id: question.question_id,
        selected_option: option,
        answer_time_seconds: elapsed,
      });
      setFeedback(res.data);
      setTimeout(() => goToNextOrFinish(sid, qs, idx + 1), 1200);
    } catch (err) {
      setError(err.message);
    }
  }, [feedback, sessionId, questions, qIndex, goToNextOrFinish]);

  useEffect(() => {
    if (phase !== "playing" || feedback) return;
    clearTimer();
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearTimer();
          handleAnswer("TIMEOUT");
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return clearTimer;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, qIndex, feedback]);

  async function handleStart() {
    setError("");
    setLoading(true);
    try {
      const res = await startGame();
      setSessionId(res.data.session_id);
      setQuestions(res.data.questions);
      setQIndex(0);
      setSelected(null);
      setFeedback(null);
      setResult(null);
      setTimeLeft(TIME_LIMIT);
      setPhase("playing");
      questionStartRef.current = Date.now();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (phase === "intro") {
    return (
      <div className="container" style={{ paddingTop: 40, paddingBottom: 60, maxWidth: 560 }}>
        <div className="card" style={{ padding: 36, textAlign: "center" }}>
          <div style={{ fontSize: 48 }}>🎮</div>
          <h2>General Knowledge Game</h2>
          <p style={{ color: "var(--gray-500)" }}>
            Answer 7 questions, 10 seconds each. Get <strong>5 or more correct</strong> to win a random
            wallet bonus between <strong>₹1 – ₹200</strong>!
          </p>
          {error && <div className="alert alert-error">{error}</div>}
          <button className="btn btn-primary" disabled={loading} onClick={handleStart} style={{ marginTop: 12 }}>
            {loading ? <span className="spinner" /> : "Start Game"}
          </button>
        </div>
      </div>
    );
  }

  if (phase === "result") {
    const passed = result.correct_answers >= 5;
    return (
      <div className="container" style={{ paddingTop: 40, paddingBottom: 60, maxWidth: 560 }}>
        <div className="card" style={{ padding: 36, textAlign: "center" }}>
          <div style={{ fontSize: 48 }}>{passed ? "🎉" : "😅"}</div>
          <h2>{passed ? "Great job!" : "Game Over"}</h2>
          <div className="grid grid-2" style={{ marginTop: 20, textAlign: "left" }}>
            <div className="card" style={{ padding: 14 }}><div style={{ fontSize: 13, color: "var(--gray-500)" }}>Correct</div><div style={{ fontSize: 22, fontWeight: 700, color: "var(--green)" }}>{result.correct_answers}</div></div>
            <div className="card" style={{ padding: 14 }}><div style={{ fontSize: 13, color: "var(--gray-500)" }}>Incorrect</div><div style={{ fontSize: 22, fontWeight: 700, color: "var(--red)" }}>{result.incorrect_answers}</div></div>
            <div className="card" style={{ padding: 14 }}><div style={{ fontSize: 13, color: "var(--gray-500)" }}>Score</div><div style={{ fontSize: 22, fontWeight: 700 }}>{result.score}/{result.max_score}</div></div>
            <div className="card" style={{ padding: 14 }}><div style={{ fontSize: 13, color: "var(--gray-500)" }}>Total Questions</div><div style={{ fontSize: 22, fontWeight: 700 }}>{result.total_questions}</div></div>
          </div>
          {result.reward_earned ? (
            <div className="alert alert-success" style={{ marginTop: 18, fontSize: 16 }}>
              🎁 You won <strong>₹{result.reward_amount}</strong>! It's been added to your wallet.
            </div>
          ) : (
            <div className="alert alert-info" style={{ marginTop: 18 }}>
              Get 5+ correct next time to earn a wallet reward.
            </div>
          )}
          <button className="btn btn-primary" onClick={handleStart} style={{ marginTop: 10 }}>Play Again</button>
        </div>
      </div>
    );
  }

  // playing
  const progressPct = ((qIndex) / questions.length) * 100;
  return (
    <div className="container" style={{ paddingTop: 30, paddingBottom: 60, maxWidth: 560 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, color: "var(--gray-500)", marginBottom: 6 }}>
        <span>Question {qIndex + 1} of {questions.length}</span>
        <span style={{ color: timeLeft <= 3 ? "var(--red)" : "var(--gray-500)", fontWeight: 700 }}>⏱ {timeLeft}s</span>
      </div>
      <div style={{ height: 6, background: "var(--gray-100)", borderRadius: 3, marginBottom: 20 }}>
        <div style={{ height: "100%", width: `${progressPct}%`, background: "var(--orange)", borderRadius: 3, transition: "width 0.3s" }} />
      </div>

      <div className="card" style={{ padding: 26 }}>
        <h3 style={{ marginBottom: 20 }}>{currentQuestion.question}</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {Object.entries(currentQuestion.options).map(([key, text]) => {
            let bg = "var(--white)", border = "var(--gray-300)", color = "var(--ink)";
            if (feedback) {
              if (key === feedback.correct_option) { bg = "var(--success-bg-soft)"; border = "var(--green)"; color = "var(--success-text-soft)"; }
              else if (key === selected) { bg = "var(--error-bg-soft)"; border = "var(--red)"; color = "var(--error-text-soft)"; }
            } else if (key === selected) {
              bg = "var(--orange-light)"; border = "var(--orange)";
            }
            return (
              <button
                key={key}
                disabled={!!feedback}
                onClick={() => handleAnswer(key)}
                className="btn"
                style={{ background: bg, border: `1.5px solid ${border}`, color, justifyContent: "flex-start", textAlign: "left", padding: "12px 16px" }}
              >
                <strong style={{ marginRight: 8 }}>{key}.</strong> {text}
              </button>
            );
          })}
        </div>
        {error && <div className="alert alert-error" style={{ marginTop: 14 }}>{error}</div>}
      </div>
    </div>
  );
}
