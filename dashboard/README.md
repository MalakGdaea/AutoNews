# AutoNews Dashboard

Next.js 14 dashboard for monitoring generated posts and manually uploading ready videos.

## Features

- Monitor post volume and status
- Recharts visualizations for 7-day frequency + status distribution
- "Ready to Upload" queue:
  - video preview
  - copy caption + hashtags
  - copy video path
  - mark as manually uploaded
- Topic preferences panel (stored in browser localStorage)

## Setup

1. Install dependencies:

```bash
cd dashboard
npm install
```

2. Create `.env.local` from `.env.example`:

```env
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
PROJECT_ROOT=C:/Users/malak/Desktop/AutoNews
```

3. Start dev server:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Data expectations

Reads from Supabase table `videos`:

- `id`
- `title`
- `script`
- `video_path`
- `video_url`
- `status`
- `created_at`

Manual upload action updates `status` to `manual_uploaded`.

For topic targeting, create `pipeline_settings` once:

```sql
create table if not exists public.pipeline_settings (
  key text primary key,
  value jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
```

The dashboard uses key `conflict_topics` in this table, and `agent/monitor.py` reads the same record before selecting stories.

## Notes

- Video preview prefers `video_url` (Supabase Storage).
- Local preview is served from `${PROJECT_ROOT}/output` only.
- If `video_path` points outside `output/`, preview is blocked for safety.
