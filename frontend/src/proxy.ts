import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Auth is handled client-side by the (protected)/layout.tsx AuthProvider.
// The proxy passes all requests through — cookie-based server-side checks
// don't work with cross-origin auth (backend on :8000, frontend on :3000).
export async function proxy(req: NextRequest): Promise<NextResponse> {
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$).*)"],
};
