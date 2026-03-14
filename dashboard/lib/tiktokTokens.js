import { getSupabaseServerClient } from "@/lib/supabaseAdmin";

const TOKEN_TABLE = "tiktok_tokens";
const TOKEN_ID = "primary";

function computeExpiry(secondsFromNow) {
  if (!secondsFromNow || Number.isNaN(Number(secondsFromNow))) return null;
  const expiresAt = new Date(Date.now() + Number(secondsFromNow) * 1000);
  return expiresAt.toISOString();
}

export async function saveTikTokTokens(tokenPayload) {
  const supabase = getSupabaseServerClient();
  const now = new Date().toISOString();
  const payload = {
    id: TOKEN_ID,
    access_token: tokenPayload.access_token || null,
    refresh_token: tokenPayload.refresh_token || null,
    expires_at: computeExpiry(tokenPayload.expires_in),
    refresh_expires_at: computeExpiry(tokenPayload.refresh_expires_in),
    scope: tokenPayload.scope || null,
    token_type: tokenPayload.token_type || null,
    open_id: tokenPayload.open_id || null,
    updated_at: now,
  };

  const { error } = await supabase.from(TOKEN_TABLE).upsert(payload, { onConflict: "id" });
  if (error) {
    throw new Error(`Failed to store TikTok tokens: ${error.message}`);
  }
}

export async function loadTikTokTokens() {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase.from(TOKEN_TABLE).select("*").eq("id", TOKEN_ID).single();
  if (error) {
    throw new Error(`Failed to load TikTok tokens: ${error.message}`);
  }
  return data;
}
