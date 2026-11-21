"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/field";
import { exportBundle, previewImport } from "@/lib/export-import";
import { prettyState } from "@/lib/storage";
import { downloadText } from "@/lib/utils";
import { useCareerStore } from "@/store/career-store";

export function BackupDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const state = useCareerStore((s) => s.state);
  const importState = useCareerStore((s) => s.importState);
  const resetState = useCareerStore((s) => s.resetState);
  const loadDemo = useCareerStore((s) => s.loadDemo);
  const persistNow = useCareerStore((s) => s.persistNow);
  const [paste, setPaste] = useState("");
  const preview = useMemo(() => (paste.trim() ? previewImport(paste, state) : null), [paste, state]);

  const json = useMemo(() => JSON.stringify(exportBundle(state), null, 2), [state]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent title="Backup / Restore" description="JSON export includes schema version and timestamp. Never silently overwrite.">
        <div className="space-y-4 text-[13px]">
          <section className="card-2 p-3">
            <h3 className="mb-2 font-medium text-white">JSON Export</h3>
            <p className="mb-3 text-slate-400">Full-state export. Schema v{state.version}.</p>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                onClick={() => {
                  void navigator.clipboard.writeText(json);
                  toast.success("Copied JSON");
                }}
              >
                Copy JSON
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  downloadText(`ai-career-os-${new Date().toISOString().slice(0, 10)}.json`, json);
                  void persistNow();
                }}
              >
                Download JSON
              </Button>
            </div>
          </section>

          <section className="card-2 p-3">
            <h3 className="mb-2 font-medium text-white">JSON Import</h3>
            <Textarea rows={6} value={paste} onChange={(e) => setPaste(e.target.value)} placeholder="Paste JSON or choose a file…" />
            <input
              className="mt-2 block text-xs text-slate-400"
              type="file"
              accept="application/json,.json"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                setPaste(await file.text());
              }}
            />
            {preview ? (
              <div className="mt-2 rounded-lg border border-white/10 p-2 text-xs">
                {preview.valid ? (
                  <p className="text-emerald-300">
                    Valid · skills {preview.counts.skills} · projects {preview.counts.projects} · jobs {preview.counts.applications}
                    {preview.duplicateHints.length ? ` · ${preview.duplicateHints.join(" ")}` : ""}
                  </p>
                ) : (
                  <p className="text-rose-300">{preview.errors.join("; ")}</p>
                )}
              </div>
            ) : null}
            <label className="mt-3 flex items-center gap-2 text-xs text-slate-400">
              <input
                type="checkbox"
                id="backup-before"
                defaultChecked
                className="accent-cyan-400"
              />
              Create backup before import
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={!preview?.valid}
                onClick={() => {
                  const backupFirst = (document.getElementById("backup-before") as HTMLInputElement | null)?.checked;
                  if (backupFirst) downloadText(`ai-career-os-pre-import.json`, prettyState(state));
                  if (!confirm("Replace current workspace with imported state?")) return;
                  importState(paste);
                  toast.success("Workspace imported");
                  onOpenChange(false);
                }}
              >
                Import (replace)
              </Button>
            </div>
          </section>

          <section className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="danger"
              onClick={() => {
                downloadText(`ai-career-os-pre-reset.json`, prettyState(state));
                if (!confirm("Reset application? A JSON backup will download first.")) return;
                resetState();
                toast.message("Workspace reset");
              }}
            >
              Reset Application
            </Button>
            <Button size="sm" variant="outline" onClick={() => { loadDemo(); toast.message("Demo workspace loaded"); onOpenChange(false); }}>
              Restore Demo Workspace
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                downloadText(`ai-career-os-pre-clean.json`, prettyState(state));
                resetState();
                toast.message("Started clean");
                onOpenChange(false);
              }}
            >
              Start Clean
            </Button>
          </section>
          <p className="text-xs text-slate-500">
            This app stores career data in the browser. A public Vercel URL does not automatically sync or back up that data.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
