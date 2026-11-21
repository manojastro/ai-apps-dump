import type { CareerOSState, JobApplication } from "@/types/career";
import { findDuplicateJobs } from "./duplicates";
import { createId, nowIso, timestamps } from "./ids";
import { active } from "./utils";

export function toCsv(rows: Record<string, string | number | boolean | undefined>[]) {
  if (rows.length === 0) return "";
  const headers = [...new Set(rows.flatMap((r) => Object.keys(r)))];
  const escape = (v: unknown) => {
    const s = v === undefined || v === null ? "" : String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  return [headers.join(","), ...rows.map((r) => headers.map((h) => escape(r[h])).join(","))].join("\n");
}

export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"' && text[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else if (c === '"') inQuotes = false;
      else cur += c;
    } else if (c === '"') inQuotes = true;
    else if (c === ",") {
      row.push(cur);
      cur = "";
    } else if (c === "\n") {
      row.push(cur.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      cur = "";
    } else cur += c;
  }
  if (cur.length || row.length) {
    row.push(cur.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.filter((r) => r.some((cell) => cell.trim()));
}

export function exportJobsCsv(state: CareerOSState) {
  return toCsv(
    active(state.applications).map((j) => ({
      company: j.company,
      role: j.role,
      tier: j.tier,
      platform: j.platform,
      status: j.status,
      dateApplied: j.dateApplied,
      nextFollowUpDate: j.nextFollowUpDate,
      jobUrl: j.jobUrl ?? "",
      location: j.location ?? "",
      referral: j.referralContact ?? "",
    })),
  );
}

export function exportContactsCsv(state: CareerOSState) {
  return toCsv(
    active(state.contacts).map((c) => ({
      name: c.name,
      designation: c.designation,
      company: c.company,
      medium: c.medium,
      status: c.status,
      contactDate: c.contactDate,
      nextTouchpointDate: c.nextTouchpointDate ?? "",
    })),
  );
}

export function exportSkillsCsv(state: CareerOSState) {
  return toCsv(
    active(state.skills).map((s) => ({
      name: s.name,
      category: s.category,
      status: s.status,
      sourceLearned: s.sourceLearned,
      mappedRoles: s.mappedRoles.join("|"),
    })),
  );
}

export function exportProjectsCsv(state: CareerOSState) {
  return toCsv(
    active(state.projects).map((p) => ({
      title: p.title,
      category: p.category,
      status: p.status,
      maturity: p.maturity,
      targetRole: p.targetRole,
      githubUrl: p.githubUrl,
      liveUrl: p.liveUrl,
    })),
  );
}

export interface CsvMapping {
  company: string;
  role: string;
  platform?: string;
  status?: string;
  dateApplied?: string;
  jobUrl?: string;
  tier?: string;
  location?: string;
}

export interface CsvPreviewRow {
  index: number;
  data: Partial<JobApplication>;
  valid: boolean;
  errors: string[];
  duplicate: boolean;
  kind: "new" | "update" | "invalid";
}

const STATUSES = ["Identified", "Referred", "Applied", "Screening", "Technical", "Offer", "Rejected"] as const;
const TIERS = ["GCC", "Enterprise IT", "AI Startup", "Consulting"] as const;

export function previewJobCsv(text: string, mapping: CsvMapping, existing: JobApplication[]): CsvPreviewRow[] {
  const table = parseCsv(text);
  if (table.length < 2) return [];
  const header = table[0]!.map((h) => h.trim());
  const idx = (name?: string) => (name ? header.findIndex((h) => h.toLowerCase() === name.toLowerCase()) : -1);
  return table.slice(1).map((cells, i) => {
    const get = (name?: string) => {
      const n = idx(name);
      return n >= 0 ? (cells[n] ?? "").trim() : "";
    };
    const company = get(mapping.company);
    const role = get(mapping.role);
    const errors: string[] = [];
    if (!company) errors.push("company required");
    if (!role) errors.push("role required");
    const statusRaw = get(mapping.status) || "Identified";
    const status = STATUSES.find((s) => s.toLowerCase() === statusRaw.toLowerCase());
    if (!status) errors.push("invalid status");
    const tierRaw = get(mapping.tier) || "AI Startup";
    const tier = TIERS.find((t) => t.toLowerCase() === tierRaw.toLowerCase()) ?? "AI Startup";
    const data: Partial<JobApplication> = {
      company,
      role,
      platform: get(mapping.platform) || "CSV Import",
      status: status ?? "Identified",
      dateApplied: get(mapping.dateApplied) || nowIso().slice(0, 10),
      jobUrl: get(mapping.jobUrl) || undefined,
      tier,
      location: get(mapping.location) || undefined,
      notes: "Imported from CSV",
      nextFollowUpDate: "",
    };
    const dupes = company && role ? findDuplicateJobs({ company, role, jobUrl: data.jobUrl, location: data.location, id: "tmp" }, existing) : [];
    return {
      index: i + 2,
      data,
      valid: errors.length === 0,
      errors,
      duplicate: dupes.length > 0,
      kind: errors.length ? "invalid" : dupes.length ? "update" : "new",
    };
  });
}

export function rowsToApplications(rows: CsvPreviewRow[], existing: JobApplication[]): JobApplication[] {
  const stamp = timestamps();
  return rows
    .filter((r) => r.valid)
    .map((r) => {
      const dupe = findDuplicateJobs(
        { company: r.data.company ?? "", role: r.data.role ?? "", jobUrl: r.data.jobUrl, location: r.data.location, id: "tmp" },
        existing,
      )[0];
      if (dupe) {
        return { ...dupe, ...r.data, updatedAt: stamp.updatedAt } as JobApplication;
      }
      return {
        id: createId("job"),
        ...stamp,
        company: r.data.company ?? "",
        tier: r.data.tier ?? "AI Startup",
        role: r.data.role ?? "",
        platform: r.data.platform ?? "CSV Import",
        jobUrl: r.data.jobUrl,
        dateApplied: r.data.dateApplied ?? stamp.createdAt.slice(0, 10),
        nextFollowUpDate: r.data.nextFollowUpDate ?? "",
        status: r.data.status ?? "Identified",
        notes: r.data.notes ?? "",
        location: r.data.location,
      } satisfies JobApplication;
    });
}
