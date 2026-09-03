import { useState, useRef, useEffect } from "react";
import { askAiAssistant } from "../../services/endpoints";
import { useAuthority } from "../../hooks/AuthorityContext";

const SUGGESTIONS = [
  "What food should I order?",
  "Show vegetarian food under ₹300",
  "What is my current order status?",
  "What is my loyalty rank?",
  "How many points do I need for the next rank?",
  "How much have I spent so far?",
];

const SpeechRecognitionApi = typeof window !== "undefined" ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;

export default function AiAssistantPage() {
  const { can, loaded } = useAuthority();
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm your QuickBite AI Assistant 🍽️ Ask me about food, your orders, loyalty points, or your cart." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // ---- Voice Ordering: browser Web Speech API, no server/API key involved ----
  const [listening, setListening] = useState(false);
  const [pendingTranscript, setPendingTranscript] = useState(""); // shown for confirmation before sending
  const [voiceError, setVoiceError] = useState("");
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!SpeechRecognitionApi) return; // unsupported browser -- graceful fallback, text input still works
    const recognition = new SpeechRecognitionApi();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setPendingTranscript(transcript);
      setListening(false);
    };
    recognition.onerror = (event) => {
      setListening(false);
      setVoiceError(
        event.error === "not-allowed" || event.error === "permission-denied"
          ? "Microphone permission was denied. You can still type your message below."
          : "Couldn't hear that clearly. Please try again or type your message."
      );
    };
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    return () => recognition.abort();
  }, []);

  function startListening() {
    if (!recognitionRef.current || loading) return;
    setVoiceError("");
    setPendingTranscript("");
    setListening(true);
    try {
      recognitionRef.current.start();
    } catch {
      setListening(false);
    }
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setListening(false);
  }

  function confirmVoiceMessage() {
    const text = pendingTranscript;
    setPendingTranscript("");
    send(text);
  }

  function editVoiceMessage() {
    setInput(pendingTranscript);
    setPendingTranscript("");
  }

  function discardVoiceMessage() {
    setPendingTranscript("");
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Authority Management can disable AI Assistant access per customer.
  // This is a UX redirect only -- the backend independently returns 403
  // on the API itself, so this can never be bypassed by skipping this check.
  if (loaded && !can("customer.ai_assistant")) {
    return (
      <div className="container" style={{ paddingTop: 40, maxWidth: 600 }}>
        <div className="empty-state">
          <h3>AI Assistant unavailable</h3>
          <p>Access to the AI Assistant has been restricted on your account by the administrator.</p>
        </div>
      </div>
    );
  }

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || loading) return;

    const history = messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));

    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setInput("");
    setLoading(true);

    try {
      const res = await askAiAssistant(message, history);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply }]);
    } catch (err) {
      const msg = err.response?.data?.error || err.message || "Something went wrong.";
      setMessages((prev) => [...prev, { role: "assistant", content: `⚠️ ${msg}`, isError: true }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 40, maxWidth: 760 }}>
      <h2>🤖 AI Assistant</h2>
      <p style={{ color: "var(--gray-500)", marginTop: -8, marginBottom: 18 }}>
        Ask about food, restaurants, your orders, or your loyalty points.
      </p>

      <div
        className="card"
        style={{
          padding: 0, display: "flex", flexDirection: "column",
          height: "60vh", minHeight: 420, overflow: "hidden",
        }}
      >
        <div style={{ flex: 1, overflowY: "auto", padding: 18, display: "flex", flexDirection: "column", gap: 12 }}>
          {messages.map((m, idx) => (
            <div
              key={idx}
              style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "80%",
                background: m.role === "user" ? "var(--orange)" : m.isError ? "var(--error-bg-soft)" : "var(--gray-100)",
                color: m.role === "user" ? "#fff" : m.isError ? "var(--error-text-soft)" : "var(--ink)",
                borderRadius: 14,
                borderBottomRightRadius: m.role === "user" ? 4 : 14,
                borderBottomLeftRadius: m.role === "user" ? 14 : 4,
                padding: "10px 14px",
                whiteSpace: "pre-wrap",
                lineHeight: 1.45,
                fontSize: 15,
              }}
            >
              {m.content}
            </div>
          ))}

          {loading && (
            <div style={{ alignSelf: "flex-start", display: "flex", gap: 4, padding: "10px 14px" }}>
              <span className="typing-dot" />
              <span className="typing-dot" style={{ animationDelay: "0.15s" }} />
              <span className="typing-dot" style={{ animationDelay: "0.3s" }} />
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {messages.length <= 1 && !pendingTranscript && (
          <div style={{ padding: "0 16px 12px", display: "flex", flexWrap: "wrap", gap: 8 }}>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="btn btn-outline btn-sm"
                style={{ fontSize: 12.5 }}
                onClick={() => send(s)}
                disabled={loading}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {voiceError && (
          <div style={{ margin: "0 16px 10px", fontSize: 13, color: "var(--red)" }}>{voiceError}</div>
        )}

        {pendingTranscript && (
          <div className="card" style={{ margin: "0 16px 12px", padding: 12, background: "var(--gray-50, #fafafa)" }}>
            <div style={{ fontSize: 12.5, color: "var(--gray-500)", marginBottom: 4 }}>🎤 Heard you say:</div>
            <div style={{ fontSize: 14.5, marginBottom: 10 }}>&ldquo;{pendingTranscript}&rdquo;</div>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={confirmVoiceMessage}>Send</button>
              <button className="btn btn-outline btn-sm" onClick={editVoiceMessage}>Edit first</button>
              <button className="btn btn-ghost btn-sm" onClick={discardVoiceMessage}>Discard</button>
            </div>
          </div>
        )}

        <form
          onSubmit={(e) => { e.preventDefault(); send(); }}
          style={{ display: "flex", gap: 8, padding: 14, borderTop: "1px solid var(--gray-100)" }}
        >
          {SpeechRecognitionApi && can("customer.voice_ordering") ? (
            <button
              type="button"
              className="btn btn-sm"
              onClick={listening ? stopListening : startListening}
              disabled={loading}
              title={listening ? "Stop listening" : "Voice Order"}
              style={{
                background: listening ? "#e63946" : "var(--gray-100)",
                color: listening ? "#fff" : "var(--ink)",
                border: "none", borderRadius: "50%", width: 42, height: 42, flexShrink: 0, fontSize: 18,
              }}
            >
              🎤
            </button>
          ) : null}
          <input
            className="input"
            style={{ flex: 1 }}
            placeholder={listening ? "Listening..." : "Ask me anything about QuickBite..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading || listening}
          />
          <button className="btn btn-primary" type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>

      <style>{`
        .typing-dot {
          width: 7px; height: 7px; border-radius: 50%;
          background: var(--gray-500); display: inline-block;
          animation: bounce 1s infinite;
        }
        @keyframes bounce { 0%, 80%, 100% { opacity: 0.3; } 40% { opacity: 1; } }
      `}</style>
    </div>
  );
}
