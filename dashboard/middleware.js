import { NextResponse } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabaseServer";

const PUBLIC_PATHS = ["/login", "/auth/tiktok", "/tiktokD8cHwfRlsVCMK4v01pvpiMagMatmvT52.txt"];
function isPublicRoute(pathname) {
  return PUBLIC_PATHS.some((path) => pathname.startsWith(path));
}

export async function middleware(request) {
  const response = NextResponse.next({ request });
  const supabase = createSupabaseServerClient(request, response);
  const {
    data: { user }
  } = await supabase.auth.getUser();

  const pathname = request.nextUrl.pathname;
  const isPublic = isPublicRoute(pathname);

  if (!user && !isPublic) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", `${pathname}${request.nextUrl.search}`);
    return NextResponse.redirect(loginUrl);
  }

  if (user && pathname === "/login") {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = "/";
    redirectUrl.searchParams.delete("next");
    return NextResponse.redirect(redirectUrl);
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|txt)$).*)"]
};
