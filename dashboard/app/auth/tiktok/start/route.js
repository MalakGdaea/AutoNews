import { NextResponse } from "next/server";
import crypto from "node:crypto";

export const dynamic = "force-dynamic";

const AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/";
const SCOPES = "video.publish,video.upload";

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing ${name} env var`);
  }
  return value;
}

function toHexSha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function base64Url(bytes) {
  return Buffer.from(bytes).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

export async function GET() {
  const clientKey = requireEnv("TIKTOK_CLIENT_KEY");
  const redirectUri = requireEnv("TIKTOK_REDIRECT_URI");

  const state = base64Url(crypto.randomBytes(16));
  const codeVerifier = base64Url(crypto.randomBytes(64));
  const codeChallenge = toHexSha256(codeVerifier);

  const url = new URL(AUTH_URL);
  url.searchParams.set("client_key", clientKey);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", SCOPES);
  url.searchParams.set("state", state);
  url.searchParams.set("code_challenge", codeChallenge);
  url.searchParams.set("code_challenge_method", "S256");

  const response = NextResponse.redirect(url.toString());
  const cookieOptions = {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 10,
  };

  response.cookies.set("tiktok_oauth_state", state, cookieOptions);
  response.cookies.set("tiktok_code_verifier", codeVerifier, cookieOptions);
  return response;
}
