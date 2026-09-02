import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/AuthContext";
import { useCart } from "../hooks/CartContext";
import { useAuthority } from "../hooks/AuthorityContext";
import ThemeToggle from "./ThemeToggle";

// Everything beyond the pinned links lives in the "More" panel, grouped by
// what a customer is actually trying to do rather than dumped as one flat
// list of emoji-prefixed links.
const MORE_GROUPS = [
  {
    label: "Plan & discover",
    items: [
      { to: "/meal-planner", label: "Meal Planner", permission: "customer.meal_planner" },
      { to: "/recipe-to-order", label: "Recipe-to-Order", permission: "customer.recipe_to_order" },
      { to: "/photo-reorder", label: "Photo Reorder", permission: "customer.photo_reorder" },
      { to: "/chefs-specials", label: "Chef's Specials", permission: "customer.chefs_specials" },
      { to: "/surplus-deals", label: "Surplus Deals", permission: "customer.surplus_deals" },
      { to: "/scheduled-orders", label: "Scheduled Orders", permission: "customer.scheduled_orders" },
      { to: "/group-orders", label: "Group Orders", permission: "customer.group_ordering" },
    ],
  },
  {
    label: "Rewards & perks",
    items: [
      { to: "/loyalty", label: "Loyalty", permission: "customer.loyalty" },
      { to: "/quickbite-pass", label: "QuickBite Pass", permission: "customer.quickbite_pass" },
      { to: "/referrals", label: "Refer & Earn", permission: "customer.referrals" },
      { to: "/food-streak", label: "Streak", permission: "customer.food_streaks" },
      { to: "/game", label: "GK Game", permission: null },
    ],
  },
  {
    label: "Track & manage",
    items: [
      { to: "/wallet", label: "Wallet", permission: "customer.wallet" },
      { to: "/favorites", label: "Favorites", permission: "customer.favorites" },
      { to: "/nutrition", label: "Nutrition", permission: "customer.nutrition_tracking" },
      { to: "/disputes", label: "Disputes", permission: "customer.disputes" },
      { to: "/ai-assistant", label: "AI Assistant", permission: "customer.ai_assistant" },
    ],
  },
];

export default function CustomerNavbar() {
  const { user, logout } = useAuth();
  const { itemCount } = useCart();
  const { can } = useAuthority();
  const navigate = useNavigate();

  const [moreOpen, setMoreOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const moreRef = useRef(null);
  const accountRef = useRef(null);

  useEffect(() => {
    function onClick(e) {
      if (moreRef.current && !moreRef.current.contains(e.target)) setMoreOpen(false);
      if (accountRef.current && !accountRef.current.contains(e.target)) setAccountOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function visible(item) {
    return item.permission === null || can(item.permission);
  }

  const groupsWithVisibleItems = MORE_GROUPS
    .map((group) => ({ ...group, items: group.items.filter(visible) }))
    .filter((group) => group.items.length > 0);

  const initials = (user?.name || "?")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header style={{ background: "var(--white)", borderBottom: "1px solid var(--gray-100)", position: "sticky", top: 0, zIndex: 20 }}>
      <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px", gap: 24 }}>
        <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", flexShrink: 0 }}>
          <span style={{
            width: 34, height: 34, borderRadius: "50%", background: "var(--orange)", color: "var(--white)",
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 700,
            fontFamily: "\"Times New Roman\", Times, serif",
          }}>Q</span>
          <span style={{ fontSize: 21, fontWeight: 700, color: "var(--ink)", letterSpacing: 0.2 }}>QuickBite</span>
        </Link>

        {user && !user.needs_profile_completion ? (
          <nav style={{ display: "flex", alignItems: "center", gap: 28, flex: 1, justifyContent: "flex-end" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
              <Link to="/" className="navlink">Browse</Link>
              {can("customer.view_orders") && <Link to="/orders" className="navlink">Orders</Link>}
              {can("customer.manage_addresses") && <Link to="/addresses" className="navlink">Addresses</Link>}

              {groupsWithVisibleItems.length > 0 && (
                <div ref={moreRef} style={{ position: "relative" }}>
                  <button
                    className="navlink"
                    onClick={() => setMoreOpen((v) => !v)}
                    style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, padding: 0 }}
                  >
                    More
                    <span style={{ fontSize: 10, marginTop: 1, transform: moreOpen ? "rotate(180deg)" : "none", transition: "transform 0.15s ease" }}>▾</span>
                  </button>

                  {moreOpen && (
                    <div className="card" style={{
                      position: "absolute", top: "calc(100% + 14px)", right: 0, width: 560,
                      padding: 22, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20,
                      boxShadow: "var(--shadow-lg)", zIndex: 30,
                    }}>
                      {groupsWithVisibleItems.map((group) => (
                        <div key={group.label}>
                          <div style={{ fontSize: 12.5, fontWeight: 700, color: "var(--gray-500)", marginBottom: 10 }}>
                            {group.label}
                          </div>
                          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {group.items.map((item) => (
                              <Link
                                key={item.to}
                                to={item.to}
                                onClick={() => setMoreOpen(false)}
                                style={{ color: "var(--ink)", fontSize: 15, textDecoration: "none" }}
                                className="navlink-dropdown-item"
                              >
                                {item.label}
                              </Link>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <Link to="/cart" style={{ position: "relative", display: "flex", alignItems: "center", color: "var(--ink)", textDecoration: "none" }}>
              <span className="navlink" style={{ padding: "8px 14px", border: "1.5px solid var(--gray-300)", borderRadius: 999, fontSize: 14.5 }}>
                Cart{itemCount > 0 ? ` · ${itemCount}` : ""}
              </span>
            </Link>

            <ThemeToggle variant="navbar" />

            <div ref={accountRef} style={{ position: "relative" }}>
              <button
                onClick={() => setAccountOpen((v) => !v)}
                style={{
                  display: "flex", alignItems: "center", gap: 9, background: "none", border: "none",
                  cursor: "pointer", padding: "4px 4px 4px 4px",
                }}
              >
                <span style={{
                  width: 32, height: 32, borderRadius: "50%", background: "var(--ink-static)", color: "#fff",
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700,
                }}>{initials}</span>
                <span style={{ fontSize: 15, color: "var(--ink)" }}>{user.name?.split(" ")[0]}</span>
                <span style={{ fontSize: 10, color: "var(--gray-500)", transform: accountOpen ? "rotate(180deg)" : "none", transition: "transform 0.15s ease" }}>▾</span>
              </button>

              {accountOpen && (
                <div className="card" style={{
                  position: "absolute", top: "calc(100% + 14px)", right: 0, width: 200,
                  padding: 8, boxShadow: "var(--shadow-lg)", zIndex: 30,
                }}>
                  <Link to="/profile" onClick={() => setAccountOpen(false)} className="navlink-dropdown-item" style={{ display: "block", padding: "9px 12px", borderRadius: 8, color: "var(--ink)", textDecoration: "none", fontSize: 15 }}>
                    Profile
                  </Link>
                  {can("customer.wallet") && (
                    <Link to="/wallet" onClick={() => setAccountOpen(false)} className="navlink-dropdown-item" style={{ display: "block", padding: "9px 12px", borderRadius: 8, color: "var(--ink)", textDecoration: "none", fontSize: 15 }}>
                      Wallet
                    </Link>
                  )}
                  <div style={{ height: 1, background: "var(--gray-100)", margin: "6px 0" }} />
                  <button
                    onClick={() => { setAccountOpen(false); logout(); navigate("/"); }}
                    style={{ display: "block", width: "100%", textAlign: "left", padding: "9px 12px", borderRadius: 8, border: "none", background: "none", color: "var(--red)", fontSize: 15, cursor: "pointer" }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--gray-50)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "none")}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </nav>
        ) : user && user.needs_profile_completion ? (
          // Brand-new Google sign-up that hasn't finished onboarding yet --
          // show nothing but Logout so they can't wander into pages that
          // need a complete profile before they've set one up.
          <nav style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ color: "var(--gray-500)", fontSize: 14 }}>Finish setting up your account</span>
            <ThemeToggle variant="navbar" />
            <button className="btn btn-ghost btn-sm" onClick={() => { logout(); navigate("/"); }}>Logout</button>
          </nav>
        ) : (
          <nav style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <ThemeToggle variant="navbar" />
            <Link to="/login" className="btn btn-outline btn-sm">Login</Link>
            <Link to="/register" className="btn btn-primary btn-sm">Sign Up</Link>
          </nav>
        )}
      </div>

      <style>{`
        .navlink {
          color: var(--gray-700);
          font-size: 15px;
          text-decoration: none;
          transition: color 0.12s ease;
        }
        .navlink:hover { color: var(--orange-dark); text-decoration: none; }
        .navlink-dropdown-item:hover { background: var(--gray-50); text-decoration: none; }
      `}</style>
    </header>
  );
}
