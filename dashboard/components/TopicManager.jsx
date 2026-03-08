"use client";

import { useEffect, useState } from "react";

export default function TopicManager() {
  const [primaryInput, setPrimaryInput] = useState("");
  const [secondaryInput, setSecondaryInput] = useState("");
  const [threshold, setThreshold] = useState(5);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");
  const [primaryTerms, setPrimaryTerms] = useState([]);
  const [secondaryTerms, setSecondaryTerms] = useState([]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch("/api/topics");
        const body = await res.json();
        if (!res.ok) throw new Error(body.error || "Failed to load topics.");
        setPrimaryTerms(body.config.primary_terms || []);
        setSecondaryTerms(body.config.secondary_terms || []);
        setThreshold(body.config.relevance_threshold || 5);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function addTerm(type) {
    const value = (type === "primary" ? primaryInput : secondaryInput).trim().toLowerCase();
    if (!value) return;
    if (type === "primary") {
      if (primaryTerms.includes(value)) return;
      setPrimaryTerms((prev) => [...prev, value]);
      setPrimaryInput("");
      return;
    }
    if (secondaryTerms.includes(value)) return;
    setSecondaryTerms((prev) => [...prev, value]);
    setSecondaryInput("");
  }

  function removeTerm(type, term) {
    if (type === "primary") {
      setPrimaryTerms((prev) => prev.filter((t) => t !== term));
      return;
    }
    setSecondaryTerms((prev) => prev.filter((t) => t !== term));
  }

  async function saveTopics() {
    setSaving(true);
    setError("");
    setOk("");
    try {
      const res = await fetch("/api/topics", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_terms: primaryTerms,
          secondary_terms: secondaryTerms,
          relevance_threshold: threshold
        })
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Failed to save topics.");
      setOk("Saved. New videos will use this targeting.");
      setTimeout(() => setOk(""), 1800);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="glass animate-rise rounded-2xl p-4 shadow-panel md:p-5">
      <h2 className="text-lg font-semibold">Conflict Topic Targeting</h2>
      <p className="mt-1 text-sm text-muted">Shared with Python monitor via Supabase. Changes apply to next pipeline run.</p>

      {loading && <p className="mt-3 text-sm text-muted">Loading topics...</p>}
      {error && <p className="mt-3 rounded-lg border border-danger/40 bg-danger/10 p-2 text-sm text-red-300">{error}</p>}
      {ok && <p className="mt-3 rounded-lg border border-accent/50 bg-accent/10 p-2 text-sm text-emerald-300">{ok}</p>}

      <div className="mt-4 space-y-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted">Primary Terms (high weight)</p>
          <div className="mt-2 flex gap-2">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-accent focus:outline-none"
              value={primaryInput}
              onChange={(e) => setPrimaryInput(e.target.value)}
              placeholder="e.g. iran"
            />
            <button type="button" onClick={() => addTerm("primary")} className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-zinc-950">
              Add
            </button>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {primaryTerms.map((term) => (
              <button
                key={`p-${term}`}
                type="button"
                onClick={() => removeTerm("primary", term)}
                className="rounded-full border border-zinc-600 px-3 py-1 text-sm text-zinc-200 transition hover:border-danger hover:text-danger"
                title="Remove term"
              >
                {term}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-muted">Secondary Terms (context weight)</p>
          <div className="mt-2 flex gap-2">
            <input
              className="w-full rounded-lg border border-zinc-700 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-accent focus:outline-none"
              value={secondaryInput}
              onChange={(e) => setSecondaryInput(e.target.value)}
              placeholder="e.g. red sea"
            />
            <button type="button" onClick={() => addTerm("secondary")} className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-zinc-950">
              Add
            </button>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {secondaryTerms.map((term) => (
              <button
                key={`s-${term}`}
                type="button"
                onClick={() => removeTerm("secondary", term)}
                className="rounded-full border border-zinc-600 px-3 py-1 text-sm text-zinc-200 transition hover:border-danger hover:text-danger"
                title="Remove term"
              >
                {term}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-muted">Relevance Threshold</p>
          <input
            type="number"
            min={1}
            max={30}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value || 5))}
            className="mt-2 w-28 rounded-lg border border-zinc-700 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 focus:border-accent focus:outline-none"
          />
        </div>

        <button
          type="button"
          onClick={saveTopics}
          disabled={saving || loading}
          className="rounded-lg border border-accent/60 px-3 py-2 text-sm text-accent transition hover:bg-accent/10 disabled:opacity-60"
        >
          {saving ? "Saving..." : "Save Targeting"}
        </button>
      </div>
    </section>
  );
}
