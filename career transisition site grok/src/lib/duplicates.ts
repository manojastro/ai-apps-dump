import type { JobApplication } from "@/types/career";
import { normalizeName, safeUrl } from "./utils";

export function normalizeJobKey(job: Pick<JobApplication, "company" | "role" | "jobUrl" | "location">) {
  const url = safeUrl(job.jobUrl ?? "");
  const hostPath = url ? new URL(url).host + new URL(url).pathname.replace(/\/$/, "") : "";
  return {
    company: normalizeName(job.company),
    role: normalizeName(job.role),
    url: hostPath.toLowerCase(),
    location: normalizeName(job.location ?? ""),
  };
}

export function findDuplicateJobs(
  incoming: Pick<JobApplication, "company" | "role" | "jobUrl" | "location" | "id">,
  existing: JobApplication[],
) {
  const key = normalizeJobKey(incoming);
  return existing.filter((job) => {
    if (job.id === incoming.id || job.archivedAt) return false;
    const other = normalizeJobKey(job);
    if (key.url && other.url && key.url === other.url) return true;
    const companyRole = key.company === other.company && key.role === other.role;
    if (!companyRole) return false;
    if (!key.location || !other.location) return true;
    return key.location === other.location;
  });
}

export function findDuplicateContacts(
  incoming: { id?: string; name: string; company: string },
  existing: { id: string; name: string; company: string; archivedAt?: string }[],
) {
  const name = normalizeName(incoming.name);
  const company = normalizeName(incoming.company);
  return existing.filter(
    (c) => c.id !== incoming.id && !c.archivedAt && normalizeName(c.name) === name && normalizeName(c.company) === company,
  );
}
