// Service authentication for SpreadLens engine -> eve agent calls.
// The engine sends `Authorization: Bearer <EVE_SERVICE_TOKEN>`; in deployment the token comes from Secret Manager.
import { timingSafeEqual } from "node:crypto";
import { type AuthFn, withAuthChallenges } from "eve/channels/auth";

export function serviceToken(): AuthFn<Request> {
  return withAuthChallenges(
    async (request: Request) => {
      const expected = process.env.EVE_SERVICE_TOKEN;
      const header = request.headers.get("authorization") ?? "";
      if (!expected || !header.startsWith("Bearer ")) return null;
      const got = Buffer.from(header.slice(7));
      const want = Buffer.from(expected);
      if (got.length !== want.length || !timingSafeEqual(got, want)) return null;
      return {
        attributes: {},
        authenticator: "spreadlens-engine",
        principalId: "spreadlens-engine",
        principalType: "service",
      };
    },
    [{ scheme: "Bearer" }],
  );
}
