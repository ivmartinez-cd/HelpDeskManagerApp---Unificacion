import { NextResponse, type NextRequest } from "next/server";

// Next.js 16 renombró "middleware" a "proxy" — ver AGENTS.md/node_modules/next/dist/docs.
const SESSION_COOKIE_NAME = "hdm_session";
const PUBLIC_PATHS = ["/login", "/forgot-password", "/reset-password"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic = PUBLIC_PATHS.some((path) => pathname.startsWith(path));
  const hasSession = request.cookies.has(SESSION_COOKIE_NAME);

  // Chequeo barato: solo mira si la cookie existe, no si la sesión sigue
  // siendo válida — eso lo valida el layout protegido contra el backend.
  if (!isPublic && !hasSession) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|.*\\.svg$|.*\\.ico$|fonts/).*)"],
};
