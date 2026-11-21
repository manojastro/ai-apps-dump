"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <div className="card mx-auto mt-16 max-w-lg p-6">
      <h1 className="text-lg font-semibold">Something broke</h1>
      <p className="mt-2 text-[13px] text-slate-400">The OS hit a rendering error. Your stored state was not automatically reset.</p>
      <p className="mt-2 font-mono text-[12px] text-rose-300">{error.message}</p>
      <Button className="mt-4" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
