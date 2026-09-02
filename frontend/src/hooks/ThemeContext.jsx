import { createContext, useContext, useEffect, useMemo, useState, useCallback, useRef } from "react";
import { useLocation } from "react-router-dom";

const ThemeContext = createContext(null);

export const THEME_MODES = ["light", "dark", "system", "schedule"];
const DEFAULT_SCHEDULE = { start: 20, end: 6 }; // 8pm -> 6am, in 0-23 local hours

/**
 * Which "portal" a URL belongs to. Kept in sync with index.html's inline
 * anti-flash script and with App.jsx's routing -- a visitor browsing the
 * Restaurant portal and the Admin portal in the same browser gets an
 * independent theme preference for each, since they're really different
 * audiences sharing one browser.
 */
export function themeRoleForPath(pathname) {
  if (pathname.startsWith("/restaurant")) return "restaurant";
  if (pathname.startsWith("/admin")) return "admin";
  return "customer";
}

function modeStorageKey(role) {
  return `themeMode:${role}`;
}
function scheduleStorageKey(role) {
  return `themeSchedule:${role}`;
}

function readStoredMode(role) {
  try {
    const v = window.localStorage.getItem(modeStorageKey(role));
    if (THEME_MODES.includes(v)) return v;
  } catch {
    // ignore
  }
  return null;
}

function readStoredSchedule(role) {
  try {
    const raw = window.localStorage.getItem(scheduleStorageKey(role));
    if (raw) {
      const parsed = JSON.parse(raw);
      if (
        Number.isInteger(parsed?.start) && parsed.start >= 0 && parsed.start <= 23 &&
        Number.isInteger(parsed?.end) && parsed.end >= 0 && parsed.end <= 23
      ) {
        return parsed;
      }
    }
  } catch {
    // ignore
  }
  return DEFAULT_SCHEDULE;
}

function isWithinSchedule(hours, now = new Date()) {
  const h = now.getHours();
  const { start, end } = hours;
  if (start === end) return false;
  if (start < end) return h >= start && h < end;
  // Wraps past midnight, e.g. 20 -> 6
  return h >= start || h < end;
}

function prefersDarkSystem() {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches;
}

function resolveTheme(mode, scheduleHours, systemPrefersDark) {
  if (mode === "dark") return "dark";
  if (mode === "light") return "light";
  if (mode === "system") return systemPrefersDark ? "dark" : "light";
  if (mode === "schedule") return isWithinSchedule(scheduleHours) ? "dark" : "light";
  return "light";
}

export function ThemeProvider({ children }) {
  const location = useLocation();
  const role = themeRoleForPath(location.pathname);

  // mode: the user's stored *preference* for the current portal ("light" |
  // "dark" | "system" | "schedule"). Falls back to "schedule" the very
  // first time a portal is visited (nobody has picked yet), so a first-time
  // visitor automatically gets Dark Mode after sunset / before sunrise
  // without having to find the toggle first.
  const [mode, setModeState] = useState(() => readStoredMode(role) ?? "schedule");
  const [scheduleHours, setScheduleHoursState] = useState(() => readStoredSchedule(role));
  const [systemPrefersDark, setSystemPrefersDark] = useState(prefersDarkSystem);
  const [tick, setTick] = useState(0); // forces re-resolution while in "schedule" mode

  // Re-read stored preference whenever we cross into a different portal
  // (customer <-> restaurant <-> admin) so each keeps its own memory.
  const lastRoleRef = useRef(role);
  useEffect(() => {
    if (lastRoleRef.current === role) return;
    lastRoleRef.current = role;
    setModeState(readStoredMode(role) ?? "schedule");
    setScheduleHoursState(readStoredSchedule(role));
  }, [role]);

  // Live system-theme following, for mode === "system".
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const onChange = (e) => setSystemPrefersDark(e.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  // Re-evaluate the schedule window periodically and whenever the tab
  // regains focus, so a page left open across the 8pm/6am boundary flips
  // over on its own without needing a refresh.
  useEffect(() => {
    if (mode !== "schedule") return undefined;
    const interval = setInterval(() => setTick((t) => t + 1), 60 * 1000);
    const onVisible = () => { if (document.visibilityState === "visible") setTick((t) => t + 1); };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [mode]);

  const theme = useMemo(
    () => resolveTheme(mode, scheduleHours, systemPrefersDark),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [mode, scheduleHours, systemPrefersDark, tick]
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const setMode = useCallback((nextMode, forRole = role) => {
    const safeMode = THEME_MODES.includes(nextMode) ? nextMode : "light";
    if (forRole === role) setModeState(safeMode);
    try {
      window.localStorage.setItem(modeStorageKey(forRole), safeMode);
    } catch {
      // ignore write failures (private browsing, storage full, etc.)
    }
  }, [role]);

  const setScheduleHours = useCallback((hours, forRole = role) => {
    const safe = {
      start: Number.isInteger(hours?.start) ? Math.min(23, Math.max(0, hours.start)) : DEFAULT_SCHEDULE.start,
      end: Number.isInteger(hours?.end) ? Math.min(23, Math.max(0, hours.end)) : DEFAULT_SCHEDULE.end,
    };
    if (forRole === role) setScheduleHoursState(safe);
    try {
      window.localStorage.setItem(scheduleStorageKey(forRole), JSON.stringify(safe));
    } catch {
      // ignore
    }
  }, [role]);

  // Quick explicit flip -- used by clicking the toggle switch itself.
  // If the current mode is auto (system/schedule), the first click "takes
  // the wheel" by picking the explicit opposite of whatever is showing
  // right now, rather than silently no-oping.
  const toggleTheme = useCallback(() => {
    const next = theme === "dark" ? "light" : "dark";
    setMode(next);
  }, [theme, setMode]);

  // Global keyboard shortcut: Ctrl/Cmd + Shift + L toggles the theme from
  // anywhere in the app, regardless of which portal is focused.
  useEffect(() => {
    function onKeyDown(e) {
      const key = e.key?.toLowerCase();
      if (key === "l" && e.shiftKey && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        toggleTheme();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [toggleTheme]);

  const value = useMemo(() => ({
    theme,
    isDark: theme === "dark",
    mode,
    role,
    scheduleHours,
    setMode,
    setScheduleHours,
    toggleTheme,
  }), [theme, mode, role, scheduleHours, setMode, setScheduleHours, toggleTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
}
