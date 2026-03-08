import { getSupabaseServerClient } from "@/lib/supabaseAdmin";

const READY_STATUSES = new Set(["generated", "saved", "ready_to_upload", "upload_failed"]);

function splitCaptionAndTags(rawTitle = "") {
  const hashtags = Array.from(new Set((rawTitle.match(/#[\w_]+/g) || []).map((t) => t.toLowerCase())));
  const caption = rawTitle.replace(/#[\w_]+/g, "").trim();
  return { caption, hashtags };
}

function normalizeVideoRow(row) {
  const { caption, hashtags } = splitCaptionAndTags(row.title || "");
  return {
    id: row.id,
    title: row.title || "Untitled",
    script: row.script || "",
    videoPath: row.video_path || "",
    status: row.status || "unknown",
    createdAt: row.created_at,
    caption: caption || row.title || "",
    hashtags,
    previewUrl: row.video_path ? `/api/videos/file?path=${encodeURIComponent(row.video_path)}` : ""
  };
}

export async function getDashboardData() {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase
    .from("videos")
    .select("id,title,script,video_path,status,created_at")
    .order("created_at", { ascending: false })
    .limit(250);

  if (error) {
    throw new Error(`Supabase read failed: ${error.message}`);
  }

  const videos = (data || []).map(normalizeVideoRow);
  const now = Date.now();
  const last7Days = Array.from({ length: 7 }).map((_, i) => {
    const day = new Date(now - (6 - i) * 24 * 60 * 60 * 1000);
    const key = day.toISOString().slice(0, 10);
    return { key, label: day.toLocaleDateString("en-US", { weekday: "short" }), posts: 0 };
  });

  for (const video of videos) {
    if (!video.createdAt) continue;
    const key = new Date(video.createdAt).toISOString().slice(0, 10);
    const bucket = last7Days.find((d) => d.key === key);
    if (bucket) bucket.posts += 1;
  }

  const statusCounter = {};
  for (const video of videos) {
    statusCounter[video.status] = (statusCounter[video.status] || 0) + 1;
  }

  const readyToUpload = videos.filter((v) => READY_STATUSES.has(v.status.toLowerCase()));

  return {
    videos,
    stats: {
      total: videos.length,
      ready: readyToUpload.length,
      failed: videos.filter((v) => v.status.toLowerCase().includes("failed")).length,
      uploaded: videos.filter((v) => v.status.toLowerCase().includes("publish") || v.status.toLowerCase().includes("uploaded")).length
    },
    frequency: last7Days.map((d) => ({ day: d.label, posts: d.posts })),
    statusDistribution: Object.entries(statusCounter).map(([name, value]) => ({ name, value })),
    readyToUpload
  };
}
