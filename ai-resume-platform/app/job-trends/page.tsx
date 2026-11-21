"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { PageHero } from "@/components/shared/PageHero";
import { ModuleBridge } from "@/components/shared/ModuleBridge";
import { SetupBanner } from "@/components/shared/SetupBanner";
import { TrendingCards } from "@/components/job-trends/TrendingCards";
import { SearchFilters, type JobFilters } from "@/components/job-trends/SearchFilters";
import { JobResults } from "@/components/job-trends/JobResults";
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

  const handleSearch = useCallback(() => {
    if (filters.q.trim()) addRecentSearch(filters.q.trim());
    setActiveQuery(filters.q);
    setSearchTrigger((n) => n + 1);
  }, [filters.q]);

  const handleRecentSelect = useCallback((q: string) => {
    setFilters((prev) => ({ ...prev, q }));
    setActiveQuery(q);
    setSearchTrigger((n) => n + 1);
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-6 pb-24 pt-8 md:pt-12">
      <SetupBanner context="jobs" />

      <PageHero
        title="The market."
        subtitle="Real openings. Real compensation. Updated hourly."
      />

      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.15, ease: [0.25, 0.1, 0.25, 1] }}
        className="space-y-16"
      >
        <TrendingCards />

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
      </motion.div>

      <ModuleBridge
        title="Build your resume."
        description="Turn your experience into an ATS-ready document with AI."
        href="/resume-builder"
        cta="Open resume builder"
      />
    </div>
  );
}