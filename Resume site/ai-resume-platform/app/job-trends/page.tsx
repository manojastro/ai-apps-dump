"use client";

import { useState, useCallback, useEffect } from "react";
import { PageHero } from "@/components/shared/PageHero";
import { ModuleBridge } from "@/components/shared/ModuleBridge";
import { SetupBanner } from "@/components/shared/SetupBanner";
import { MotionPage } from "@/components/shared/MotionPage";
import { TrendingCards } from "@/components/job-trends/TrendingCards";
import { SearchFilters, type JobFilters } from "@/components/job-trends/SearchFilters";
import { JobResults } from "@/components/job-trends/JobResults";
import { LiveSearchPanel } from "@/components/job-trends/LiveSearchPanel";
import { addRecentSearch } from "@/components/job-trends/RecentSearches";

const defaultFilters: JobFilters = {
  q: "",
  domains: [],
  minCtc: 300000,
  maxCtc: 5000000,
  location: "",
};

export default function JobTrendsPage() {
  const [filters, setFilters] = useState<JobFilters>(defaultFilters);
  const [searchTrigger, setSearchTrigger] = useState(0);
  const [activeQuery, setActiveQuery] = useState("");

  // Shareable search query via URL params (no personal data)
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    const location = params.get("location");
    if (q || location) {
      setFilters((prev) => ({
        ...prev,
        q: q || prev.q,
        location: location || prev.location,
      }));
      if (q) {
        setActiveQuery(q);
        setSearchTrigger((n) => n + 1);
      }
    }
  }, []);

  const handleSearch = useCallback(() => {
    if (filters.q.trim()) addRecentSearch(filters.q.trim());
    setActiveQuery(filters.q);
    setSearchTrigger((n) => n + 1);
    if (typeof window !== "undefined") {
      const params = new URLSearchParams();
      if (filters.q.trim()) params.set("q", filters.q.trim());
      if (filters.location.trim()) params.set("location", filters.location.trim());
      const qs = params.toString();
      const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
      window.history.replaceState({}, "", url);
    }
  }, [filters.q, filters.location]);

  const handleRecentSelect = useCallback((q: string) => {
    setFilters((prev) => ({ ...prev, q }));
    setActiveQuery(q);
    setSearchTrigger((n) => n + 1);
  }, []);

  return (
    <MotionPage className="mx-auto max-w-5xl px-6 pb-24 pt-10">
      <PageHero
        title="The market."
        subtitle="Where demand is, answers with sources, and open roles across India."
      />

      <SetupBanner context="jobs" />

      <div className="space-y-14">
        <TrendingCards />

        <LiveSearchPanel />

        <section className="space-y-5">
          <div>
            <h2 className="text-[20px] font-semibold tracking-tight text-[#1d1d1f]">
              Find open roles
            </h2>
            <p className="mt-1 text-[14px] text-[#6e6e73]">
              Search public listings. Open a result to apply on the source site.
            </p>
          </div>
          <SearchFilters
            filters={filters}
            onChange={setFilters}
            onSearch={handleSearch}
            onRecentSelect={handleRecentSelect}
          />
          <JobResults
            filters={filters}
            searchTrigger={searchTrigger}
            searchQuery={activeQuery}
          />
        </section>
      </div>

      <ModuleBridge
        title="Build your resume."
        description="Turn your experience into an ATS-ready document with AI."
        href="/resume-builder"
        cta="Open resume builder"
      />
    </MotionPage>
  );
}
