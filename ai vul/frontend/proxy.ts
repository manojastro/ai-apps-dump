/**
 * Request-time guard: unauthenticated visitors are redirected to /login.
 * This only checks that a session cookie exists - the backend validates it on every API call,
 * and every permission is enforced server-side.
 */
import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const hasSession = request.cookies.has("aegis_session");
  const { pathname, search } = request.nextUrl;
  if (!hasSession && pathname !== "/login") {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }
  // An existing (possibly expired) cookie never bounces /login, so a stale session cannot cause a redirect loop.
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|icon.svg).*)"],
};
