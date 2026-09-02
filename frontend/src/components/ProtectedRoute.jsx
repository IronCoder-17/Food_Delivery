import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/AuthContext";

export default function ProtectedRoute({ roles, allowIncompleteProfile, children }) {
  const { user, role } = useAuth();

  if (!user) {
    const loginPath = roles?.includes("admin")
      ? "/admin/login"
      : roles?.includes("restaurant")
      ? "/restaurant/login"
      : "/login";
    return <Navigate to={loginPath} replace />;
  }

  if (roles && !roles.includes(role)) {
    // Logged in but wrong role - never allow customer -> restaurant/admin APIs or vice versa
    const home = role === "admin" ? "/admin" : role === "restaurant" ? "/restaurant" : "/";
    return <Navigate to={home} replace />;
  }

  // A brand-new Google customer must finish supplying mobile/address/state/
  // city before using the rest of the app -- send them to /complete-profile
  // from anywhere else, except the completion page itself.
  if (role === "customer" && user?.needs_profile_completion && !allowIncompleteProfile) {
    return <Navigate to="/complete-profile" replace />;
  }

  return children;
}
