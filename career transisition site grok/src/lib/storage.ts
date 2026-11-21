import { IDB_ATTACHMENTS, IDB_NAME, LKG_KEY, RECOVERY_KEY, STORAGE_KEY, SYNC_CHANNEL } from "./constants";
import { createEmptyState } from "./empty-state";
import { nowIso } from "./ids";
import { migrateState, needsMigration } from "./migrations";
import { parseCareerState, stripSecrets } from "./validation";
import type { CareerOSState, RecoveryPayload } from "@/types/career";

export type LoadResult =
  | { ok: true; state: CareerOSState; migrated: boolean }
  | { ok: false; recovery: RecoveryPayload };

export interface StorageRepository {
  load(): Promise<LoadResult>;
  save(state: CareerOSState): Promise<void>;
  backup(state: CareerOSState): Promise<string>;
  restore(state: CareerOSState): Promise<CareerOSState>;
  readCorrupted(): string | null;
  writeRecoveryCopy(raw: string): void;
}

function memoryFallback() {
  const g = globalThis as unknown as { __careerOsMem?: Map<string, string> };
  if (!g.__careerOsMem) g.__careerOsMem = new Map();
  return g.__careerOsMem;
}

function getRaw(key: string): string | null {
  try {
    if (typeof localStorage !== "undefined") return localStorage.getItem(key);
  } catch {
    /* private mode */
  }
  return memoryFallback().get(key) ?? null;
}

function setRaw(key: string, value: string) {
  try {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(key, value);
      return;
    }
  } catch {
    /* quota or private */
  }
  memoryFallback().set(key, value);
}

function delRaw(key: string) {
  try {
    if (typeof localStorage !== "undefined") localStorage.removeItem(key);
  } catch {
    /* ignore */
  }
  memoryFallback().delete(key);
}

export function serializeState(state: CareerOSState) {
  const clean = stripSecrets(state);
  return JSON.stringify(clean);
}

export function prettyState(state: CareerOSState) {
  return JSON.stringify(stripSecrets(state), null, 2);
}

function persistLkg(state: CareerOSState) {
  const parsed = parseCareerState(state);
  if (!parsed.success) return;
  setRaw(LKG_KEY, serializeState(parsed.data));
}

export class LocalStorageRepository implements StorageRepository {
  async load(): Promise<LoadResult> {
    const raw = getRaw(STORAGE_KEY);
    if (!raw) {
      return { ok: true, state: createEmptyState(), migrated: false };
    }
    let parsedJson: unknown;
    try {
      parsedJson = JSON.parse(raw);
    } catch {
      return {
        ok: false,
        recovery: {
          reason: "Stored JSON is corrupted and could not be parsed.",
          corruptedJson: raw,
          canRestoreLkg: Boolean(getRaw(LKG_KEY)),
        },
      };
    }

    if (needsMigration(parsedJson)) {
      this.writeRecoveryCopy(raw);
      const migrated = migrateState(parsedJson);
      const checked = parseCareerState(migrated);
      if (!checked.success) {
        return {
          ok: false,
          recovery: {
            reason: "Migration produced an invalid state. Restore last-known-good or import a backup.",
            corruptedJson: raw,
            canRestoreLkg: Boolean(getRaw(LKG_KEY)),
          },
        };
      }
      return { ok: true, state: checked.data, migrated: true };
    }

    const checked = parseCareerState(parsedJson);
    if (!checked.success) {
      return {
        ok: false,
        recovery: {
          reason: "Stored state failed schema validation. Nothing was overwritten.",
          corruptedJson: raw,
          canRestoreLkg: Boolean(getRaw(LKG_KEY)),
        },
      };
    }
    return { ok: true, state: checked.data, migrated: false };
  }

  async save(state: CareerOSState): Promise<void> {
    const checked = parseCareerState(state);
    if (!checked.success) {
      throw new Error("Refusing to persist invalid state.");
    }
    const next: CareerOSState = {
      ...checked.data,
      meta: { ...checked.data.meta, lastSavedAt: nowIso(), updatedAt: nowIso() },
    };
    setRaw(STORAGE_KEY, serializeState(next));
    persistLkg({ ...next, meta: { ...next.meta, lastKnownGoodAt: nowIso() } });
  }

  async backup(state: CareerOSState): Promise<string> {
    const json = prettyState({
      ...state,
      meta: { ...state.meta, lastBackupAt: nowIso(), updatedAt: nowIso() },
    });
    persistLkg(state);
    return json;
  }

  async restore(state: CareerOSState): Promise<CareerOSState> {
    const checked = parseCareerState(state);
    if (!checked.success) throw new Error("Imported state failed validation.");
    await this.save(checked.data);
    return checked.data;
  }

  readCorrupted(): string | null {
    return getRaw(RECOVERY_KEY) ?? getRaw(STORAGE_KEY);
  }

  writeRecoveryCopy(raw: string) {
    setRaw(RECOVERY_KEY, raw);
  }
}

export async function restoreLastKnownGood(repo: StorageRepository): Promise<CareerOSState> {
  const raw = getRaw(LKG_KEY);
  if (!raw) throw new Error("No last-known-good snapshot exists.");
  const json = JSON.parse(raw) as unknown;
  const migrated = migrateState(json);
  const checked = parseCareerState(migrated);
  if (!checked.success) throw new Error("Last-known-good snapshot is not valid.");
  await repo.restore(checked.data);
  return checked.data;
}

export function clearAllKeys() {
  delRaw(STORAGE_KEY);
  delRaw(LKG_KEY);
  delRaw(RECOVERY_KEY);
}

let channel: BroadcastChannel | null = null;

export function subscribeCrossTab(onRemote: (state: CareerOSState) => void) {
  const handler = (event: StorageEvent) => {
    if (event.key !== STORAGE_KEY || !event.newValue) return;
    const parsed = parseCareerState(JSON.parse(event.newValue) as unknown);
    if (parsed.success) onRemote(parsed.data);
  };
  if (typeof window !== "undefined") window.addEventListener("storage", handler);

  if (typeof BroadcastChannel !== "undefined") {
    channel = new BroadcastChannel(SYNC_CHANNEL);
    channel.onmessage = (ev: MessageEvent<unknown>) => {
      const parsed = parseCareerState(ev.data);
      if (parsed.success) onRemote(parsed.data);
    };
  }

  return () => {
    if (typeof window !== "undefined") window.removeEventListener("storage", handler);
    channel?.close();
    channel = null;
  };
}

export function publishCrossTab(state: CareerOSState) {
  channel?.postMessage(stripSecrets(state));
}

export function newerState(local: CareerOSState, remote: CareerOSState) {
  return (remote.meta.updatedAt || "") > (local.meta.updatedAt || "");
}

export function openAttachmentDb(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === "undefined") return Promise.resolve(null);
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_NAME, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(IDB_ATTACHMENTS)) {
        req.result.createObjectStore(IDB_ATTACHMENTS, { keyPath: "id" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export const defaultRepository = new LocalStorageRepository();
