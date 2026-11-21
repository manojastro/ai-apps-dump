// BFF proxy: browser -> /api/engine/<path> -> engine /api/<path>, adding the bearer token from the httpOnly cookie
// and a correlation id. Bodies (JSON, multipart uploads, PNG pages, XLSX/PDF downloads) are streamed through unchanged.
import { type NextRequest } from "next/server";
import { engineFetch } from "@/lib/server";

const PASS_HEADERS = ["content-type", "content-disposition", "x-snapshot-hash", "x-snapshot-stale", "x-page-width-pt",
  "x-page-height-pt", "x-correlation-id", "cache-control"];

async function proxy(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  if (path.some((p) => p === ".." || p.includes("\\"))) return new Response("Bad path", { status: 400 });
  const url = `/api/${path.map(encodeURIComponent).join("/")}${req.nextUrl.search}`;
  const headers: Record<string, string> = {};
  const ct = req.headers.get("content-type");
  if (ct) headers["content-type"] = ct;
  const cid = req.headers.get("x-correlation-id");
  if (cid) headers["x-correlation-id"] = cid;
  const hasBody = !["GET", "HEAD"].includes(req.method);
  const res = await engineFetch(url, {
    method: req.method,
    headers,
    body: hasBody ? await req.arrayBuffer() : undefined,
  });
  const out = new Headers();
  for (const h of PASS_HEADERS) {
    const v = res.headers.get(h);
    if (v) out.set(h, v);
  }
  return new Response(res.body, { status: res.status, headers: out });
}

export { proxy as GET, proxy as POST, proxy as DELETE, proxy as PUT, proxy as PATCH };
