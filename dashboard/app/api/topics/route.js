import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabaseAdmin";

const DEFAULT_TOPIC_CONFIG = {
  primary_terms: ["iran", "israel", "gaza", "hamas", "hezbollah", "idf", "tehran"],
  secondary_terms: [
    "united states",
    "us",
    "u.s.",
    "america",
    "pentagon",
    "white house",
    "middle east",
    "red sea",
    "houthis",
    "syria",
    "lebanon",
    "iraq",
    "yemen",
    "missile",
    "drone",
    "strike",
    "retaliation",
    "ceasefire",
    "sanctions",
    "nuclear"
  ],
  relevance_threshold: 5
};

function normalizeTerms(input) {
  if (!Array.isArray(input)) return [];
  return Array.from(
    new Set(
      input
        .map((item) => String(item).trim().toLowerCase())
        .filter(Boolean)
    )
  );
}

export async function GET() {
  try {
    const supabase = getSupabaseServerClient();
    const { data, error } = await supabase
      .from("pipeline_settings")
      .select("value")
      .eq("key", "conflict_topics")
      .limit(1);

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    if (!data?.length) return NextResponse.json({ config: DEFAULT_TOPIC_CONFIG });

    return NextResponse.json({
      config: {
        primary_terms: normalizeTerms(data[0]?.value?.primary_terms || DEFAULT_TOPIC_CONFIG.primary_terms),
        secondary_terms: normalizeTerms(data[0]?.value?.secondary_terms || DEFAULT_TOPIC_CONFIG.secondary_terms),
        relevance_threshold: Number(data[0]?.value?.relevance_threshold || DEFAULT_TOPIC_CONFIG.relevance_threshold)
      }
    });
  } catch (error) {
    return NextResponse.json({ error: error.message || "Unexpected error." }, { status: 500 });
  }
}

export async function PUT(request) {
  try {
    const body = await request.json();
    const config = {
      primary_terms: normalizeTerms(body?.primary_terms),
      secondary_terms: normalizeTerms(body?.secondary_terms),
      relevance_threshold: Number(body?.relevance_threshold || DEFAULT_TOPIC_CONFIG.relevance_threshold)
    };

    if (!config.primary_terms.length) {
      return NextResponse.json({ error: "At least one primary term is required." }, { status: 400 });
    }
    if (!Number.isFinite(config.relevance_threshold) || config.relevance_threshold < 1) {
      return NextResponse.json({ error: "relevance_threshold must be >= 1." }, { status: 400 });
    }

    const supabase = getSupabaseServerClient();
    const { error } = await supabase.from("pipeline_settings").upsert(
      {
        key: "conflict_topics",
        value: config,
        updated_at: new Date().toISOString()
      },
      {
        onConflict: "key"
      }
    );

    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json({ ok: true, config });
  } catch (error) {
    return NextResponse.json({ error: error.message || "Unexpected error." }, { status: 500 });
  }
}
