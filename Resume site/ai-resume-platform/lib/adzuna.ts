import { getCached, setCache } from "./cache";
import { formatCtc } from "./utils";

const BASE_URL = "https://api.adzuna.com/v1/api/jobs/in";

function getCredentials() {
  const appId = process.env.ADZUNA_APP_ID;
  const appKey = process.env.ADZUNA_APP_KEY;
  if (!appId || !appKey) {
    throw new Error("ADZUNA_APP_ID and ADZUNA_APP_KEY must be configured");
  }
  return { appId, appKey };
}

export interface NormalizedJob {
  id: string;
  title: string;
  company: string;
  location: string;
  ctcMin: number | null;
  ctcMax: number | null;
  ctcDisplay: string;
  postedDate: string;
  url: string;
  description: string;
}

interface AdzunaJob {
  id: string;
  title: string;
  company?: { display_name?: string };
  location?: { display_name?: string };
  salary_min?: number;
  salary_max?: number;
  created?: string;
  redirect_url?: string;
  description?: string;
}

interface AdzunaSearchResponse {
  count: number;
  results: AdzunaJob[];
}

function normalizeJob(job: AdzunaJob): NormalizedJob {
  const ctcMin = job.salary_min ?? null;
  const ctcMax = job.salary_max ?? null;
  let ctcDisplay = "Not disclosed";
  if (ctcMin && ctcMax) {
    ctcDisplay = `${formatCtc(ctcMin)} – ${formatCtc(ctcMax)}`;
  } else if (ctcMin) {
    ctcDisplay = `From ${formatCtc(ctcMin)}`;
  } else if (ctcMax) {
    ctcDisplay = `Up to ${formatCtc(ctcMax)}`;
  }

  return {
    id: String(job.id),
    title: job.title,
    company: job.company?.display_name ?? "Unknown",
    location: job.location?.display_name ?? "India",
    ctcMin,
    ctcMax,
    ctcDisplay,
    postedDate: job.created ?? "",
    url: job.redirect_url ?? "#",
    description: job.description ?? "",
  };
}

async function adzunaFetch<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const { appId, appKey } = getCredentials();
  const url = new URL(`${BASE_URL}${path}`);
  url.searchParams.set("app_id", appId);
  url.searchParams.set("app_key", appKey);
  for (const [k, v] of Object.entries(params)) {
    if (v) url.searchParams.set(k, v);
  }

  const res = await fetch(url.toString(), { next: { revalidate: 3600 } });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Adzuna API error ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export async function searchJobs(params: {
  q?: string;
  location?: string;
  minCtc?: number;
  maxCtc?: number;
  page?: number;
}): Promise<{ jobs: NormalizedJob[]; total: number }> {
  const cacheKey = `search:${JSON.stringify(params)}`;
  const cached = getCached<{ jobs: NormalizedJob[]; total: number }>(cacheKey);
  if (cached) return cached;

  const queryParams: Record<string, string> = {
    results_per_page: "20",
    sort_by: "date",
  };
  if (params.q) queryParams.what = params.q;
  if (params.location) queryParams.where = params.location;
  if (params.minCtc) queryParams.salary_min = String(params.minCtc);
  if (params.maxCtc) queryParams.salary_max = String(params.maxCtc);

  const page = params.page ?? 1;
  const data = await adzunaFetch<AdzunaSearchResponse>(
    `/search/${page}`,
    queryParams
  );

  const result = {
    jobs: data.results.map(normalizeJob),
    total: data.count,
  };
  setCache(cacheKey, result);
  return result;
}

export async function fetchSampleJobs(
  query: string,
  count = 50
): Promise<NormalizedJob[]> {
  const cacheKey = `sample:${query}:${count}`;
  const cached = getCached<NormalizedJob[]>(cacheKey);
  if (cached) return cached;

  const data = await adzunaFetch<AdzunaSearchResponse>("/search/1", {
    what: query,
    results_per_page: String(count),
    sort_by: "date",
  });

  const jobs = data.results.map(normalizeJob);
  setCache(cacheKey, jobs);
  return jobs;
}

export async function getSalaryHistogram(
  query: string
): Promise<{ min: number; max: number; mean: number } | null> {
  const cacheKey = `histogram:${query}`;
  const cached = getCached<{ min: number; max: number; mean: number }>(cacheKey);
  if (cached) return cached;

  try {
    const data = await adzunaFetch<{
      histogram: Record<string, number>;
      mean: number;
    }>("/histogram", { what: query });

    const buckets = Object.keys(data.histogram).map(Number);
    if (buckets.length === 0) return null;

    const result = {
      min: Math.min(...buckets),
      max: Math.max(...buckets),
      mean: data.mean,
    };
    setCache(cacheKey, result);
    return result;
  } catch {
    return null;
  }
}

export interface TrendingDomainData {
  id: string;
  name: string;
  icon: string;
  rank: number;
  /** Real vacancy count only when source is Adzuna; 0 for Exa/mock */
  openingCount: number;
  ctcMin: number | null;
  ctcMax: number | null;
  ctcDisplay: string;
  trendDirection: "up" | "down" | "stable";
  trendPercent: number;
  blurb: string;
  /** Qualitative demand signal from web research (Exa+LLM) — not a vacancy count */
  signal?: "strong" | "moderate" | "limited";
  keySkills?: string[];
}

export async function fetchCategories(): Promise<
  { tag: string; label: string }[]
> {
  const cacheKey = "categories";
  const cached = getCached<{ tag: string; label: string }[]>(cacheKey);
  if (cached) return cached;

  const data = await adzunaFetch<{ results: { tag: string; label: string }[] }>(
    "/categories"
  );
  setCache(cacheKey, data.results);
  return data.results;
}