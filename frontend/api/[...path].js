const API_ORIGIN = process.env.RENDER_API_URL || "https://breathesg-vafh.onrender.com";

export const config = {
  api: { bodyParser: false },
};

async function readBody(req) {
  if (req.method === "GET" || req.method === "HEAD") return undefined;
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

export default async function handler(req, res) {
  const segments = req.query.path;
  const path = Array.isArray(segments) ? segments.join("/") : segments || "";
  const qs = req.url?.includes("?") ? req.url.slice(req.url.indexOf("?")) : "";
  const target = `${API_ORIGIN}/api/${path}${qs}`;

  try {
    const headers = { ...req.headers };
    delete headers.host;
    delete headers.connection;
    delete headers["content-length"];

    const body = await readBody(req);
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
    });

    res.status(upstream.status);
    upstream.headers.forEach((value, key) => {
      const lower = key.toLowerCase();
      if (lower === "transfer-encoding" || lower === "connection") return;
      res.setHeader(key, value);
    });

    const out = Buffer.from(await upstream.arrayBuffer());
    res.send(out);
  } catch (err) {
    res.status(502).json({ detail: "API proxy error", error: err.message });
  }
}
