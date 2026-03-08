"use client";

import { useEffect, useState } from "react";

const KEY = "autonews_topics";

export default function TopicManager() {
  const [topics, setTopics] = useState(["Breaking", "Politics", "Global"]);
  const [input, setInput] = useState("");

  useEffect(() => {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length) setTopics(parsed);
      } catch {
        // ignore parse issues and keep defaults
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(topics));
  }, [topics]);

  function addTopic() {
    const value = input.trim();
    if (!value) return;
    if (topics.includes(value)) return;
    setTopics((prev) => [...prev, value]);
    setInput("");
  }

  function removeTopic(topic) {
    setTopics((prev) => prev.filter((t) => t !== topic));
  }

  return (
    <section className="glass animate-rise rounded-2xl p-4 shadow-panel md:p-5">
      <h2 className="text-lg font-semibold">Topics Configuration</h2>
      <p className="mt-1 text-sm text-muted">Local preferences for what you want to prioritize in your next scripts.</p>

      <div className="mt-4 flex gap-2">
        <input
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-accent focus:outline-none"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Add a topic, e.g. Markets"
        />
        <button type="button" onClick={addTopic} className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-zinc-950">
          Add
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {topics.map((topic) => (
          <button
            key={topic}
            type="button"
            onClick={() => removeTopic(topic)}
            className="rounded-full border border-zinc-600 px-3 py-1 text-sm text-zinc-200 transition hover:border-danger hover:text-danger"
            title="Remove topic"
          >
            {topic}
          </button>
        ))}
      </div>
    </section>
  );
}
