import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { getMyAuthorities } from "../services/endpoints";
import { useAuth } from "./AuthContext";

const AuthorityContext = createContext(null);

// Frontend gating is a UX convenience ONLY (hide/disable buttons for a
// cleaner experience). The real, unbypassable enforcement happens on the
// backend via @require_permission on each protected route -- see
// backend/services/authority_service.py. Even if this context is empty or
// stale, the backend will still return 403 for a restricted action.
export function AuthorityProvider({ children }) {
  const { user, role } = useAuth();
  const [authorities, setAuthorities] = useState({});
  const [loaded, setLoaded] = useState(false);

  const refreshAuthorities = useCallback(async () => {
    if (role !== "customer") {
      setAuthorities({});
      setLoaded(true);
      return;
    }
    try {
      const res = await getMyAuthorities();
      setAuthorities(res.data || {});
    } catch (e) {
      // If the check itself fails, default to permissive UI -- the backend
      // will still enforce correctly on the actual API call.
      setAuthorities({});
    } finally {
      setLoaded(true);
    }
  }, [role]);

  useEffect(() => {
    if (user && role === "customer") {
      refreshAuthorities();
    } else {
      setAuthorities({});
      setLoaded(true);
    }
  }, [user, role, refreshAuthorities]);

  const can = useCallback(
    (key) => {
      if (!loaded) return true; // avoid UI flicker while loading; backend still enforces
      if (!(key in authorities)) return true; // unknown key -> don't block UI, backend governs it
      return !!authorities[key];
    },
    [authorities, loaded]
  );

  return (
    <AuthorityContext.Provider value={{ authorities, can, loaded, refreshAuthorities }}>
      {children}
    </AuthorityContext.Provider>
  );
}

export function useAuthority() {
  const ctx = useContext(AuthorityContext);
  if (!ctx) throw new Error("useAuthority must be used within AuthorityProvider");
  return ctx;
}
