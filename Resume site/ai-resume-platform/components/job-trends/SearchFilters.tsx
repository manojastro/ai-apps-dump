"use client";

import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { RecentSearches } from "./RecentSearches";
import { JOB_DOMAINS } from "@/lib/domains";
import { cn } from "@/lib/utils";

export interface JobFilters {
  q: string;
  domains: string[];
  minCtc: number;
  maxCtc: number;
  location: string;
}

interface SearchFiltersProps {
  filters: JobFilters;
  onChange: (filters: JobFilters) => void;
  onSearch: () => void;
  onRecentSelect?: (query: string) => void;
}

const CTC_MIN = 300000;
const CTC_MAX = 5000000;

export function SearchFilters({
  filters,
  onChange,
  onSearch,
  onRecentSelect,
}: SearchFiltersProps) {
  // Search supports one domain at a time, so selecting replaces rather than adds.
  const selectDomain = (id: string) => {
    const domains = filters.domains.includes(id) ? [] : [id];
    onChange({ ...filters, domains });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          placeholder="Role, skill, or company"
          className="flex-1 focus-ring"
          value={filters.q}
          onChange={(e) => onChange({ ...filters, q: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          aria-label="Search jobs"
        />
        <Input
          placeholder="Location"
          className="focus-ring sm:w-44"
          value={filters.location}
          onChange={(e) => onChange({ ...filters, location: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          aria-label="Location filter"
        />
        <Button onClick={onSearch} size="lg" className="shrink-0">
          Search
        </Button>
      </div>

      <RecentSearches
        onSelect={
          onRecentSelect ||
          ((q) => {
            onChange({ ...filters, q });
            onSearch();
          })
        }
      />

      <div className="flex flex-wrap gap-2">
        {JOB_DOMAINS.map((d) => (
          <button
            key={d.id}
            type="button"
            onClick={() => selectDomain(d.id)}
            aria-pressed={filters.domains.includes(d.id)}
            className={cn(
              "rounded-full px-3.5 py-1.5 text-[12px] font-medium transition-colors duration-200 focus-ring",
              filters.domains.includes(d.id)
                ? "bg-[#1d1d1f] text-white"
                : "bg-[#1d1d1f]/[0.04] text-[#6e6e73] hover:text-[#1d1d1f]"
            )}
          >
            {d.name}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-4 pt-1">
        <p className="w-32 shrink-0 text-[12px] text-[#6e6e73]">
          ₹{(filters.minCtc / 100000).toFixed(0)}L — ₹
          {(filters.maxCtc / 100000).toFixed(0)}L
        </p>
        <Slider
          className="flex-1"
          min={CTC_MIN}
          max={CTC_MAX}
          step={100000}
          value={[filters.minCtc, filters.maxCtc]}
          onValueChange={([min, max]) =>
            onChange({ ...filters, minCtc: min, maxCtc: max })
          }
          aria-label="CTC range filter"
        />
      </div>
    </div>
  );
}
