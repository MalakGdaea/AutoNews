import { NextResponse } from "next/server";
import { saveTikTokTokens } from "@/lib/tiktokTokens";

const TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/";

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing ${name} env var`);
  }
  return value;
}

function buildErrorRedirect(requestUrl, reason) {
  const url = new URL("/", requestUrl.origin);
  url.searchParams.set("tiktok", "error");
  if (reason) {
    url.searchParams.set("reason", reason);
  }
  return NextResponse.redirect(url);
}

export async function GET(request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const state = requestUrl.searchParams.get("state");
  const error = requestUrl.searchParams.get("error");
  const errorDescription = requestUrl.searchParams.get("error_description");

  if (error) {
    return buildErrorRedirect(requestUrl, errorDescription || error);
  }

  if (!code) {
    return buildErrorRedirect(requestUrl, "missing_code");
  }

  const cookies = request.cookies;
  const expectedState = cookies.get("tiktok_oauth_state")?.value;
  const codeVerifier = cookies.get("tiktok_code_verifier")?.value;

  if (!state || !expectedState || state !== expectedState) {
    return buildErrorRedirect(requestUrl, "invalid_state");
  }

  if (!codeVerifier) {
    return buildErrorRedirect(requestUrl, "missing_verifier");
  }

  const clientKey = requireEnv("TIKTOK_CLIENT_KEY");
  const clientSecret = requireEnv("TIKTOK_CLIENT_SECRET");
  const redirectUri = requireEnv("TIKTOK_REDIRECT_URI");

  const body = new URLSearchParams({
    client_key: clientKey,
    client_secret: clientSecret,
    grant_type: "authorization_code",
    code,
    redirect_uri: redirectUri,
    code_verifier: codeVerifier,
  });

  let tokenPayload;
  try {
    const tokenResponse = await fetch(TOKEN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });

    tokenPayload = await tokenResponse.json();

    if (!tokenResponse.ok) {
      return buildErrorRedirect(
        requestUrl,
        tokenPayload?.error?.message || tokenPayload?.error || "token_exchange_failed"
      );
    }

    await saveTikTokTokens(tokenPayload);
  } catch (err) {
    return buildErrorRedirect(requestUrl, err.message || "token_exchange_failed");
  }

  const response = NextResponse.redirect(new URL("/", requestUrl.origin));
  response.cookies.delete("tiktok_oauth_state");
  response.cookies.delete("tiktok_code_verifier");
  return response;
}
