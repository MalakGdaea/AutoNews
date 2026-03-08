"use client";

import { useState } from "react";

export default function CopyButton({ text, label = "Copy" }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <button
      onClick={handleCopy}
      className="rounded-lg border border-zinc-700 px-3 py-1.5 text-sm text-zinc-200 transition hover:border-accent hover:text-accent"
      type="button"
    >
      {copied ? "Copied" : label}
    </button>
  );
}
