const API_ORIGIN = process.env.RENDER_API_URL || "https://breathesg-vafh.onrender.com";

export default async function middleware(request) {
  const url = new URL(request.url);
  if (!url.pathname.startsWith("/api/")) {
    return;
  }

  const target = `${API_ORIGIN}${url.pathname}${url.search}`;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");

  return fetch(target, {
    method: request.method,
    headers,
    body: request.method !== "GET" && request.method !== "HEAD" ? request.body : undefined,
  });
}

export const config = {
  matcher: ["/api/:path*"],
};
