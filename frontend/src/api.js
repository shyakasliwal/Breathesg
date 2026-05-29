// In dev, Vite proxies /api → Django (same origin, session + CSRF cookies work).
// On Vercel, use same-origin /api (see vercel.json rewrite). Do not point VITE_API_URL at
// another host — browsers block third-party session cookies.
function resolveApiBase() {
  const configured = (import.meta.env.VITE_API_URL || "").trim();
  if (!configured) return "/api";
  if (configured.startsWith("/")) {
    return configured.replace(/\/$/, "") || "/api";
  }
  try {
    const apiOrigin = new URL(configured).origin;
    if (typeof window !== "undefined" && apiOrigin !== window.location.origin) {
      console.warn(
        "[api] VITE_API_URL is cross-origin; using /api via same-origin proxy instead."
      );
      return "/api";
    }
    return configured.replace(/\/$/, "");
  } catch {
    return "/api";
  }
}

const API_BASE = resolveApiBase();
function readCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1];
}

async function ensureCsrf() {
  const response = await fetch(`${API_BASE}/auth/csrf/`, { credentials: "include" });
  const data = await response.json().catch(() => ({}));
  return data.csrfToken || readCookie("csrftoken") || "";
}

async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {}),
  };
  if (method !== "GET" && method !== "HEAD") {
    const token = await ensureCsrf();
    if (!token) {
      throw new Error("Could not obtain CSRF token");
    }
    headers["X-CSRFToken"] = token;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers,
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail || data.non_field_errors?.[0] || "Request failed";
    throw new Error(detail);
  }
  return data;
}

export const api = {
  login: (email, password) =>
    request("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request("/auth/logout/", { method: "POST" }),
  me: () => request("/me/"),
  dashboard: () => request("/dashboard/"),
  records: (params = "") => request(`/records/${params}`),
  review: (id, action, note = "") =>
    request(`/records/${id}/review/`, {
      method: "POST",
      body: JSON.stringify({ action, note }),
    }),
  ingest: (sourceType, file) => {
    const form = new FormData();
    form.append("file", file);
    return request(`/ingest/${sourceType}/`, { method: "POST", body: form });
  },
};
