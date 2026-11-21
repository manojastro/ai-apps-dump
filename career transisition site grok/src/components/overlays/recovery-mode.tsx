"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/field";
import { downloadText } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";

export function RecoveryMode() {
  const recovery = useCareerStore((s) => s.recovery);
  const restoreLkg = useCareerStore((s) => s.restoreLkg);
  const restoreBackup = useCareerStore((s) => s.restoreBackup);
  const resetState = useCareerStore((s) => s.resetState);
  const exportCorrupted = useCareerStore((s) => s.exportCorrupted);
  const [paste, setPaste] = useState("");
  if (!recovery) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#090d16] p-4">
      <div className="card w-full max-w-2xl p-6">
        <p className="text-[12px] tracking-wide text-rose-300 uppercase">Recovery Mode</p>
        <h1 className="mt-1 text-lg font-semibold">Stored state could not be trusted</h1>
        <p className="mt-2 text-[13px] text-slate-400">{recovery.reason}</p>
        <p className="mt-2 text-[13px] text-slate-500">Nothing was silently overwritten.</p>
        <div className="mt-5 grid gap-2">
          <Button
            disabled={!recovery.canRestoreLkg}
            onClick={async () => {
              await restoreLkg();
              toast.success("Restored last-known-good state");
            }}
          >
            Restore last known good state
          </Button>
          <Textarea rows={5} placeholder="Paste a backup JSON…" value={paste} onChange={(e) => setPaste(e.target.value)} />
          <Button
            variant="outline"
            disabled={!paste.trim()}
            onClick={() => {
              restoreBackup(paste);
              toast.success("Backup imported");
            }}
          >
            Import backup
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              const raw = exportCorrupted() ?? recovery.corruptedJson ?? "";
              downloadText("ai-career-os-corrupted.json", raw);
            }}
          >
            Export corrupted state for troubleshooting
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              if (!confirm("Reset the application? This does not recover the corrupted payload unless you exported it.")) return;
              resetState();
            }}
          >
            Reset application
          </Button>
        </div>
      </div>
    </div>
  );
}
