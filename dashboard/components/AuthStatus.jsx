"use client";

import { useEffect, useState } from "react";
import { createSupabaseBrowserClient } from "@/lib/supabaseClient";

export default function AuthStatus() {
  const [supabase, setSupabase] = useState(null);
  const [userEmail, setUserEmail] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setSupabase(createSupabaseBrowserClient());
  }, []);

  useEffect(() => {
    if (!supabase) return;
    let isMounted = true;

    supabase.auth.getUser().then(({ data }) => {
      if (!isMounted) return;
      setUserEmail(data.user?.email ?? "");
      setIsLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!isMounted) return;
      setUserEmail(session?.user?.email ?? "");
      setIsLoading(false);
    });

    return () => {
      isMounted = false;
      listener?.subscription?.unsubscribe();
    };
  }, [supabase]);

  const handleSignOut = async () => {
    if (!supabase) return;
    await supabase.auth.signOut();
  };

  return (
    <div className="flex items-center gap-3 text-xs text-zinc-300">
      <span className="hidden sm:inline">Signed in as</span>
      <span className="font-medium text-zinc-100">
        {isLoading ? "Loading..." : userEmail || "Unknown user"}
      </span>
      <button
        type="button"
        onClick={handleSignOut}
        className="rounded-full border border-zinc-700/70 bg-zinc-900/60 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-zinc-200 transition hover:border-zinc-500 hover:text-white"
      >
        Sign out
      </button>
    </div>
  );
}
