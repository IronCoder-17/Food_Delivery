import axios from "axios";
import { getAuthScope, tokenKey } from "../utils/authScope";

export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000/api";

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  // Each portal (customer/restaurant/admin) keeps its own token so that,
  // e.g., a restaurant dashboard open in one tab and a customer session
  // open in another don't overwrite each other's auth.
  const scope = getAuthScope(window.location.pathname);
  const token = localStorage.getItem(tokenKey(scope));
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.error ||
      err.response?.data?.message ||
      "Something went wrong. Please try again.";
    return Promise.reject({ ...err, message });
  }
);

export default api;