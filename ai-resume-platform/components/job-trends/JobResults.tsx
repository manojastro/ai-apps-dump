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

  useEffect(() => {
    if (searchTrigger === 0) return;

    const search = async () => {
      setLoading(true);
      setError(null);
      setHasSearched(true);

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
          }
        } else if (filters.domains.length > 1) {
          setError("Select only one domain filter at a time for search.");
          setLoading(false);
          return;
        }

        if (query) params.set("q", query);
        if (filters.location) params.set("location", filters.location);
        if (filters.minCtc > 300000) params.set("minCtc", String(filters.minCtc));
        if (filters.maxCtc < 5000000) params.set("maxCtc", String(filters.maxCtc));

        const res = await fetch(`/api/jobs/search?${params}`);
        if (!res.ok) throw new Error(await parseApiError(res));

        const data = await res.json();
        setJobs(data.jobs);
        setTotal(data.total);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Search error");
        setJobs([]);
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
      <div className="text-center py-8">
        <p className="text-[15px] text-[#6e6e73] leading-relaxed max-w-md mx-auto">{error}</p>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <p className="text-center text-[15px] text-[#6e6e73]">
        No results. Try different keywords or broaden your filters.
      </p>
    );
  }

  return (
    <div>
      <p className="section-label text-center mb-8">
        {total.toLocaleString("en-IN")} positions
      </p>
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
            </div>
            <div className="text-right shrink-0 ml-6">
              <p className="text-[13px] font-medium text-[#1d1d1f]">{job.ctcDisplay}</p>
              {job.postedDate && (
                <p className="text-[11px] text-[#6e6e73]/50 mt-0.5">{formatDate(job.postedDate)}</p>
              )}
            </div>
          </motion.a>
        ))}
      </div>
    </div>
  );
}