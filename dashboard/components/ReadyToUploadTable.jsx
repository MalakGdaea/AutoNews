"use client";

import { useMemo, useState } from "react";
import CopyButton from "@/components/CopyButton";

function buildUploadPackage(item) {
  const hashBlock = item.hashtags?.length ? `\n\n${item.hashtags.join(" ")}` : "";
  return `${item.caption || item.title}${hashBlock}`.trim();
}

export default function ReadyToUploadTable({ initialItems }) {
  const [items, setItems] = useState(initialItems);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState("");

  const hasItems = useMemo(() => items.length > 0, [items.length]);

  async function markManualUploaded(id) {
    setError("");
    setSavingId(id);
    try {
      const res = await fetch(`/api/videos/${id}/mark-uploaded`, {
        method: "PATCH"
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Failed to update status");
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingId(null);
    }
  }

  return (
    <section className="glass animate-rise rounded-2xl p-4 shadow-panel md:p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Ready to Upload</h2>
        <p className="text-sm text-muted">{items.length} pending</p>
      </div>

      {!hasItems && <p className="rounded-xl border border-dashed border-zinc-700 p-4 text-sm text-muted">No videos waiting for manual upload.</p>}

      {error && <p className="mb-3 rounded-lg border border-danger/40 bg-danger/10 p-2 text-sm text-red-300">{error}</p>}

      <div className="grid gap-4">
        {items.map((item) => (
          <article key={item.id} className="rounded-xl border border-zinc-700/70 bg-zinc-900/50 p-3 md:p-4">
            <div className="grid gap-4 lg:grid-cols-[minmax(220px,320px),1fr] lg:items-start">
              <div className="lg:max-w-[320px]">
                {item.previewUrl ? (
                  <div className="mx-auto aspect-[9/16] overflow-hidden rounded-[1.75rem] border border-zinc-700 bg-black shadow-[0_20px_50px_rgba(0,0,0,0.35)]">
                    <video
                      className="h-full w-full object-cover"
                      controls
                      playsInline
                      preload="metadata"
                      src={item.previewUrl}
                    />
                  </div>
                ) : (
                  <div className="flex aspect-[9/16] items-center justify-center rounded-[1.75rem] border border-dashed border-zinc-700 text-sm text-muted">
                    Preview unavailable
                  </div>
                )}
                <p className="mt-3 break-all font-[var(--font-mono)] text-xs text-muted">
                  {item.videoUrl || item.videoPath || "No file path"}
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <p className="text-sm uppercase tracking-wide text-muted">Title</p>
                  <p className="mt-1 text-base">{item.title}</p>
                </div>
                <div>
                  <p className="text-sm uppercase tracking-wide text-muted">Caption + Hashtags</p>
                  <pre className="mt-1 max-h-36 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-700/80 bg-zinc-900/70 p-2 font-[var(--font-mono)] text-sm text-zinc-200">
                    {buildUploadPackage(item)}
                  </pre>
                </div>
                <div className="flex flex-wrap gap-2">
                  <CopyButton text={buildUploadPackage(item)} label="Copy Caption" />
                  <CopyButton text={item.videoUrl || item.videoPath || ""} label="Copy Video URL" />
                  <button
                    type="button"
                    onClick={() => markManualUploaded(item.id)}
                    disabled={savingId === item.id}
                    className="rounded-lg border border-accent/60 px-3 py-1.5 text-sm text-accent transition hover:bg-accent/10 disabled:opacity-60"
                  >
                    {savingId === item.id ? "Saving..." : "Mark Uploaded"}
                  </button>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
