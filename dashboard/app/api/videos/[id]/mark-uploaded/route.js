import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@/lib/supabaseAdmin";

export async function PATCH(_request, { params }) {
  const id = Number(params.id);
  if (!Number.isFinite(id)) {
    return NextResponse.json({ error: "Invalid video id." }, { status: 400 });
  }

  try {
    const supabase = getSupabaseServerClient();
    const { error } = await supabase
      .from("videos")
      .update({ status: "manual_uploaded" })
      .eq("id", id);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ ok: true });
  } catch (error) {
    return NextResponse.json({ error: error.message || "Unexpected error." }, { status: 500 });
  }
}
