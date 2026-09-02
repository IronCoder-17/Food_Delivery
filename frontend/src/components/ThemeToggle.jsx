import { useEffect, useRef, useState } from "react";
import { useTheme } from "../hooks/ThemeContext";

const HOUR_LABELS = Array.from({ length: 24 }, (_, h) => {
  const period = h < 12 ? "AM" : "PM";
  const display = h % 12 === 0 ? 12 : h % 12;
  return `${display}:00 ${period}`;
});

const MODE_META = {
  light: { label: "Light", icon: "☀️", hint: "Always light" },
  dark: { label: "Dark", icon: "🌙", hint: "Always dark" },
  system: { label: "System", icon: "💻", hint: "Match your device" },
  schedule: { label: "Auto-schedule", icon: "🕗", hint: "Dark in the evening, light in the morning" },
};

/**
 * Light/Dark theme control.
 *
 * variant:
 *  - "navbar"   -- sits on a light navbar (customer header)
 *  - "sidebar"  -- sits on the always-dark dashboard sidebar (restaurant/admin)
 *  - "floating" -- fixed corner control for pages with no nav (auth screens)
 *
 * Clicking the switch itself is a quick explicit flip (light <-> dark).
 * The small caret opens a menu for System / Auto-schedule (8pm-6am by
 * default, customizable), matching the same shortcut as Ctrl/Cmd+Shift+L.
 */
export default function ThemeToggle({ variant = "navbar", className = "" }) {
  const { isDark, mode, scheduleHours, setMode, setScheduleHours, toggleTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    function onDocClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    }
    function onEsc(e) { if (e.key === "Escape") setOpen(false); }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  const isAuto = mode === "system" || mode === "schedule";
  const wrapperClass = `theme-toggle theme-toggle--${variant} ${className}`.trim();

  return (
    <div className={`theme-toggle-group theme-toggle-group--${variant}`} ref={menuRef}>
      <button
        type="button"
        role="switch"
        aria-checked={isDark}
        aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
        title={`${isDark ? "Switch to light" : "Switch to dark"} · Ctrl/Cmd+Shift+L`}
        className={wrapperClass}
        onClick={toggleTheme}
      >
        <span className="theme-toggle-sky" aria-hidden="true">
          <span className="theme-toggle-star" style={{ top: 5, left: 8 }} />
          <span className="theme-toggle-star" style={{ top: 14, left: 16 }} />
          <span className="theme-toggle-star" style={{ top: 8, left: 24 }} />
        </span>
        <span className="theme-toggle-thumb" aria-hidden="true">
          <span className="theme-toggle-thumb-icon theme-toggle-thumb-icon--sun">☀️</span>
          <span className="theme-toggle-thumb-icon theme-toggle-thumb-icon--moon">🌙</span>
        </span>
        {isAuto && <span className="theme-toggle-auto-dot" title={`Auto (${MODE_META[mode].label})`}>A</span>}
      </button>

      <button
        type="button"
        className={`theme-toggle-caret theme-toggle-caret--${variant}`}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Theme options"
        title="More theme options"
        onClick={() => setOpen((o) => !o)}
      >
        ▾
      </button>

      {open && (
        <div className={`theme-toggle-menu theme-toggle-menu--${variant}`} role="menu">
          <div className="theme-toggle-menu-title">Appearance</div>
          {Object.keys(MODE_META).map((key) => (
            <button
              key={key}
              type="button"
              role="menuitemradio"
              aria-checked={mode === key}
              className={`theme-toggle-menu-item ${mode === key ? "is-active" : ""}`}
              onClick={() => setMode(key)}
            >
              <span className="theme-toggle-menu-icon">{MODE_META[key].icon}</span>
              <span>
                <span className="theme-toggle-menu-label">{MODE_META[key].label}</span>
                <span className="theme-toggle-menu-hint">{MODE_META[key].hint}</span>
              </span>
              {mode === key && <span className="theme-toggle-menu-check">✓</span>}
            </button>
          ))}

          {mode === "schedule" && (
            <div className="theme-toggle-schedule">
              <div className="theme-toggle-schedule-row">
                <label>Dark from</label>
                <select
                  className="input"
                  value={scheduleHours.start}
                  onChange={(e) => setScheduleHours({ ...scheduleHours, start: Number(e.target.value) })}
                >
                  {HOUR_LABELS.map((label, h) => <option key={h} value={h}>{label}</option>)}
                </select>
              </div>
              <div className="theme-toggle-schedule-row">
                <label>Light from</label>
                <select
                  className="input"
                  value={scheduleHours.end}
                  onChange={(e) => setScheduleHours({ ...scheduleHours, end: Number(e.target.value) })}
                >
                  {HOUR_LABELS.map((label, h) => <option key={h} value={h}>{label}</option>)}
                </select>
              </div>
            </div>
          )}

          <div className="theme-toggle-menu-footer">Shortcut: Ctrl/Cmd+Shift+L</div>
        </div>
      )}
    </div>
  );
}
