"use client";

import { useEffect, useState } from "react";
import {
  formatRelativeTime,
  getLastSavedAt,
  markSessionSaved,
} from "@/lib/localWorkspace";

/**
 * Local-only save indicator. Does not upload anything.
 */
export function WorkspaceStatus({ watchKey }: { watchKey?: string }) {
  const [label, setLabel] = useState("Local workspace");

  useEffect(() => {
    markSessionSaved();
    setLabel(formatRelativeTime(Date.now()));
  }, [watchKey]);

  useEffect(() => {
    const tick = () => setLabel(formatRelativeTime(getLastSavedAt() ?? Date.now()));
    tick();
    const id = setInterval(tick, 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <p
      className="inline-flex items-center gap-1.5 text-[11px] text-[#6e6e73]"
      title="Your draft is stored only in this browser (localStorage). Nothing is uploaded for saving."
    >
      <span className="h-1.5 w-1.5 rounded-full bg-[#34c759]" aria-hidden />
      {label} · this browser only
    </p>
  );
}
