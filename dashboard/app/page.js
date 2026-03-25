import PostingFrequencyChart from "@/components/PostingFrequencyChart";
import ReadyToUploadTable from "@/components/ReadyToUploadTable";
import StatCard from "@/components/StatCard";
import StatusPieChart from "@/components/StatusPieChart";
import TopicManager from "@/components/TopicManager";
import AuthStatus from "@/components/AuthStatus";
import { getDashboardData } from "@/lib/dashboard-data";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const fetchCache = "force-no-store";

function EmptyState({ message }) {
  return (
    <section className="glass rounded-2xl p-5 shadow-panel">
      <p className="text-sm text-muted">{message}</p>
    </section>
  );
}

export default async function HomePage() {
  let payload = null;
  let error = "";

  try {
    payload = await getDashboardData();
  } catch (err) {
    error = err.message || "Failed to load dashboard data.";
  }

  return (
    <div className="space-y-6">
      <header className="animate-rise rounded-2xl border border-zinc-700/60 bg-black/20 px-4 py-5 md:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="font-[var(--font-mono)] text-xs uppercase tracking-[0.2em] text-muted">AutoNews Ops</p>
            <h1 className="mt-2 text-2xl font-semibold md:text-4xl">Manual Upload Dashboard</h1>
          </div>
          <AuthStatus />
        </div>
        <p className="mt-2 max-w-3xl text-sm text-zinc-300">
          Monitor generated posts, copy captions and hashtags, preview videos, and manually upload to TikTok from one place.
        </p>
      </header>

      {error && (
        <section className="rounded-xl border border-danger/50 bg-danger/10 p-4 text-sm text-red-300">
          {error} Check `dashboard/.env` and Supabase credentials.
        </section>
      )}

      {!error && payload && (
        <>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Total Videos" value={payload.stats.total} />
            <StatCard label="Ready To Upload" value={payload.stats.ready} tone="accent" />
            <StatCard label="Uploaded" value={payload.stats.uploaded} />
            <StatCard label="Failed" value={payload.stats.failed} tone="danger" />
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <PostingFrequencyChart data={payload.frequency} />
            <StatusPieChart data={payload.statusDistribution} />
          </section>

          <section className="grid gap-4 xl:grid-cols-[2fr,1fr]">
            {payload.readyToUpload.length > 0 ? (
              <ReadyToUploadTable initialItems={payload.readyToUpload} />
            ) : (
              <EmptyState message="No videos are currently ready to upload." />
            )}
            <TopicManager />
          </section>
        </>
      )}
    </div>
  );
}
