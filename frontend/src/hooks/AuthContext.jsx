import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { getAuthScope, tokenKey, userKey } from "../utils/authScope";

const AuthContext = createContext(null);

function loadUser(scope) {
  const raw = localStorage.getItem(userKey(scope));
  return raw ? JSON.parse(raw) : null;
}

export function AuthProvider({ children }) {
  const location = useLocation();
  const scope = getAuthScope(location.pathname);
  const [user, setUser] = useState(() => loadUser(scope));

  // Whenever navigation crosses into a different portal (customer <->
  // restaurant <-> admin), re-read that portal's own session instead of
  // reusing whatever was loaded for the previous one.
  useEffect(() => {
    setUser(loadUser(scope));
  }, [scope]);

  // Keep this tab in sync if the same portal logs in/out in another tab.
  useEffect(() => {
    function handleStorage(e) {
      if (e.key === userKey(scope)) {
        setUser(e.newValue ? JSON.parse(e.newValue) : null);
      }
    }
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [scope]);

  const login = useCallback(
    (token, userData) => {
      // Prefer the role the server actually returned; fall back to the
      // current URL's portal if a response ever omits it.
      const loginScope = userData?.role || scope;
      localStorage.setItem(tokenKey(loginScope), token);
      localStorage.setItem(userKey(loginScope), JSON.stringify(userData));
      setUser(userData);
    },
    [scope]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(tokenKey(scope));
    localStorage.removeItem(userKey(scope));
    setUser(null);
  }, [scope]);

  return (
    <AuthContext.Provider value={{ user, role: user?.role || null, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}