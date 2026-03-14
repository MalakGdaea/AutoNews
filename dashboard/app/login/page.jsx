"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createSupabaseBrowserClient } from "@/lib/supabaseClient";

const DEFAULT_REDIRECT = "/";

export default function LoginPage() {
  const [supabase, setSupabase] = useState(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState({ type: "idle", message: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectTo = searchParams.get("next") || DEFAULT_REDIRECT;
  const errorParam = searchParams.get("error");

  useEffect(() => {
    setSupabase(createSupabaseBrowserClient());
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!supabase) {
      setStatus({ type: "error", message: "Supabase client not ready. Please try again." });
      return;
    }
    setIsSubmitting(true);
    setStatus({ type: "idle", message: "" });

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setStatus({ type: "error", message: error.message });
      setIsSubmitting(false);
      return;
    }

    setStatus({
      type: "success",
      message: "Signed in successfully."
    });
    setIsSubmitting(false);
    router.replace(redirectTo);
  };

  return (
    <div className="mx-auto flex min-h-[80vh] w-full max-w-4xl items-center justify-center">
      <section className="glass w-full max-w-lg rounded-3xl p-6 shadow-panel md:p-8">
        <header className="space-y-2">
          <p className="font-[var(--font-mono)] text-xs uppercase tracking-[0.2em] text-muted">AutoNews Ops</p>
          <h1 className="text-2xl font-semibold md:text-3xl">Sign in to the dashboard</h1>
          <p className="text-sm text-zinc-300">
            Use your email + password. Access is limited to approved users in Supabase Auth.
          </p>
        </header>

        {errorParam && (
          <div className="mt-4 rounded-xl border border-danger/50 bg-danger/10 p-3 text-sm text-red-300">
            Authentication error. Please sign in again.
          </div>
        )}

        {status.message && (
          <div
            className={`mt-4 rounded-xl border p-3 text-sm ${
              status.type === "error"
                ? "border-danger/50 bg-danger/10 text-red-300"
                : "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
            }`}
          >
            {status.message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block text-xs uppercase tracking-[0.2em] text-muted">
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-xl border border-zinc-700/60 bg-zinc-900/60 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-400/60"
              placeholder="you@company.com"
              required
            />
          </label>

          <label className="block text-xs uppercase tracking-[0.2em] text-muted">
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-xl border border-zinc-700/60 bg-zinc-900/60 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-400/60"
              placeholder="••••••••"
              minLength={6}
              required
            />
          </label>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-xl bg-emerald-400/90 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Sign in
          </button>
        </form>
      </section>
    </div>
  );
}
