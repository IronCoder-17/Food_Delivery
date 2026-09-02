/**
 * The app has three independent portals (customer, restaurant, admin) that
 * can legitimately be open at the same time in different tabs of the same
 * browser -- e.g. a person browsing as a customer while also reviewing
 * their restaurant dashboard. Because localStorage is shared across all
 * tabs of the same origin, a single "fd_token" key would let logging into
 * one portal silently log the others out. Scoping storage keys by portal
 * (derived from the URL) keeps the three sessions fully independent.
 */
export function getAuthScope(pathname) {
  if (pathname.startsWith("/restaurant")) return "restaurant";
  if (pathname.startsWith("/admin")) return "admin";
  return "customer";
}

export function tokenKey(scope) {
  return `fd_token_${scope}`;
}

export function userKey(scope) {
  return `fd_user_${scope}`;
}