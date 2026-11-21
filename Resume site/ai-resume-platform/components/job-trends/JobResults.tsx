"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";
import type { NormalizedJob } from "@/lib/adzuna";
import type { JobFilters } from "./SearchFilters";
import { JOB_DOMAINS } from "@/lib/domains";

interface JobResultsProps {
  filters: JobFilters;
  searchTrigger: number;
  searchQuery?: string;
}

async function parseApiError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data.error || `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

export function JobResults({ filters, searchTrigger, searchQuery }: JobResultsProps) {
  const [jobs, setJobs] = useState<NormalizedJob[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [source, setSource] = useState<"adzuna" | "exa" | null>(null);
  const [note, setNote] = useState<string>("");

  useEffect(() => {
    if (searchTrigger === 0) return;

    const search = async () => {
      setLoading(true);
      setError(null);
      setHasSearched(true);
      setNote("");

      const q = searchQuery ?? filters.q;
      const hasDomain = filters.domains.length > 0;

      if (!q.trim() && !hasDomain) {
        setError("Enter a search term or select a domain filter.");
        setLoading(false);
        setJobs([]);
        return;
      }

      try {
        const params = new URLSearchParams();
        let query = q.trim();

        if (filters.domains.length === 1) {
          const domain = JOB_DOMAINS.find((d) => d.id === filters.domains[0]);
          if (domain) {
            query = query ? `${query} ${domain.keywords[0]}` : domain.keywords[0];
            params.set("domain", domain.id);
          }
        } else if (filters.domains.length > 1) {
          setError("Select only one domain filter at a time for search.");
          setLoading(false);
          return;
        }

        if (query) params.set("q", query);
        if (filters.location) params.set("location", filters.location);
        // CTC filters only apply to Adzuna; still send if user set them
        if (filters.minCtc > 300000) params.set("minCtc", String(filters.minCtc));
        if (filters.maxCtc < 5000000) params.set("maxCtc", String(filters.maxCtc));

        const res = await fetch(`/api/jobs/search?${params}`);
        if (!res.ok) throw new Error(await parseApiError(res));

        const data = await res.json();
        setJobs(data.jobs || []);
        setTotal(data.total ?? data.jobs?.length ?? 0);
        setSource(data.source === "exa" || data.source === "adzuna" ? data.source : null);
        setNote(typeof data.note === "string" ? data.note : "");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Search error");
        setJobs([]);
        setSource(null);
      } finally {
        setLoading(false);
      }
    };

    search();
  }, [searchTrigger, filters, searchQuery]);

  if (!hasSearched) return null;

  if (loading) {
    return (
      <div className="space-y-px">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-none" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="py-6 text-[14px] leading-relaxed text-[#6e6e73]">{error}</p>
    );
  }

  if (jobs.length === 0) {
    return (
      <p className="py-6 text-[14px] text-[#6e6e73]">
        No results. Try different keywords or broaden your filters.
      </p>
    );
  }

  return (
    <div className="pt-2">
      <p className="section-label mb-1">
        {source === "exa"
          ? `${total} web listings`
          : `${total.toLocaleString("en-IN")} positions`}
      </p>
      {note ? (
        <p className="mb-5 text-[12px] leading-relaxed text-[#6e6e73]">{note}</p>
      ) : source === "exa" ? (
        <p className="mb-5 text-[12px] leading-relaxed text-[#6e6e73]">
          Public pages found via web search — open a listing for salary and
          application details.
        </p>
      ) : null}
      <div className="divide-y divide-[#1d1d1f]/[0.06]">
        {jobs.map((job, i) => (
          <motion.a
            key={job.id}
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.03, duration: 0.4 }}
            className="group flex items-center justify-between py-5 px-2 hover:px-4 transition-all duration-300"
          >
            <div className="min-w-0 flex-1">
              <h3 className="text-[15px] font-medium text-[#1d1d1f] tracking-tight truncate group-hover:text-[#0071e3] transition-colors duration-300">
                {job.title}
              </h3>
              <p className="text-[13px] text-[#6e6e73] mt-0.5 truncate">
                {job.company} · {job.location}
              </p>
              {source === "exa" && job.description && (
                <p className="text-[12px] text-[#6e6e73]/70 mt-1 line-clamp-1">
                  {job.description}
                </p>
              )}
            </div>
            <div className="text-right shrink-0 ml-6">
              <p className="text-[13px] font-medium text-[#1d1d1f]">{job.ctcDisplay}</p>
              {job.postedDate && (
                <p className="text-[11px] text-[#6e6e73]/50 mt-0.5">
                  {formatDate(job.postedDate)}
                </p>
              )}
            </div>
          </motion.a>
        ))}
      </div>
    </div>
  );
}
