// Spending protection for the server's own API key.
//
// Requests that bring the visitor's own key (x-api-key header) are never limited: they're
// billed to the visitor. Requests that use the server's ANTHROPIC_API_KEY are limited per
// visitor (IP) per hour, plus a global daily cap, so a public link can't drain the key.
//
// In-memory only: fine for a single instance. Behind several instances (e.g. Cloud Run with
// max-instances > 1) each instance keeps its own counts, so the real cap is N x the limit.

const num = (v, d) => (Number.isFinite(Number(v)) && Number(v) >= 0 ? Number(v) : d);

export const LIMITS = {
  resumePerHour: num(process.env.LIMIT_RESUME_PER_HOUR, 5),
  chatPerHour: num(process.env.LIMIT_CHAT_PER_HOUR, 30),
  dailyTotal: num(process.env.LIMIT_DAILY_TOTAL, 300),
  requireUserKey: /^(1|true|yes)$/i.test(process.env.REQUIRE_USER_KEY || ""),
};

const HOUR = 60 * 60 * 1000;
const hits = new Map(); // `${kind}:${ip}` -> [timestamps]
let day = new Date().toDateString();
let dayCount = 0;

// Drop stale entries every 10 minutes so memory stays small
setInterval(() => {
  const cutoff = Date.now() - HOUR;
  for (const [k, arr] of hits) {
    const fresh = arr.filter((t) => t > cutoff);
    fresh.length ? hits.set(k, fresh) : hits.delete(k);
  }
}, 10 * 60 * 1000).unref();

/**
 * Express middleware factory. `kind` is "resume" or "chat".
 * Expects req.ai (set earlier by the server) with `usingServerKey`.
 */
export function aiLimit(kind) {
  const perHour = kind === "resume" ? LIMITS.resumePerHour : LIMITS.chatPerHour;
  return (req, res, next) => {
    if (!req.ai?.usingServerKey) return next(); // own key, or demo mode: nothing to protect

    const today = new Date().toDateString();
    if (today !== day) { day = today; dayCount = 0; }
    if (dayCount >= LIMITS.dailyTotal) {
      return res.status(429).json({
        error: "The free AI quota for today is used up. Add your own API key in Settings to keep going, or try again tomorrow.",
      });
    }

    const key = `${kind}:${req.ip}`;
    const now = Date.now();
    const recent = (hits.get(key) || []).filter((t) => t > now - HOUR);
    if (recent.length >= perHour) {
      const mins = Math.max(1, Math.ceil((recent[0] + HOUR - now) / 60000));
      res.set("Retry-After", String(mins * 60));
      return res.status(429).json({
        error: `You've reached the free limit of ${perHour} ${kind === "resume" ? "resumes" : "messages"} per hour. Try again in ${mins} min, or add your own API key in Settings.`,
      });
    }
    recent.push(now);
    hits.set(key, recent);
    dayCount++;
    next();
  };
}
