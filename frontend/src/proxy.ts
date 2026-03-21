import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login"];

export function proxy(req: NextRequest): NextResponse {
  const { pathname } = req.nextUrl;

  // Allow public paths through
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Check for refresh cookie — if present, user may have a valid session.
  // Proxy cannot call FastAPI here (would add latency on every route).
  // We do an optimistic check: if forge_refresh cookie exists, let through.
  // The AuthContext in the browser will call /auth/refresh on mount to verify.
  // If that fails, the (protected) layout redirects to /login client-side.
  const refreshCookie = req.cookies.get("forge_refresh");
  if (!refreshCookie) {
    const loginUrl = new URL("/login", req.nextUrl);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$).*)"],
};
