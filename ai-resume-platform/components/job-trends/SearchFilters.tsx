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

export function SearchFilters({ filters, onChange, onSearch, onRecentSelect }: SearchFiltersProps) {
  const toggleDomain = (id: string) => {
    const domains = filters.domains.includes(id)
      ? filters.domains.filter((d) => d !== id)
      : [...filters.domains, id];
    onChange({ ...filters, domains });
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row gap-3 items-center">
        <Input
          placeholder="Search roles..."
          className="flex-1"
          value={filters.q}
          onChange={(e) => onChange({ ...filters, q: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          aria-label="Search jobs"
        />
        <Button onClick={onSearch} size="lg" className="w-full sm:w-auto shrink-0">
          Search
        </Button>
      </div>

      <RecentSearches
        onSelect={onRecentSelect || ((q) => {
          onChange({ ...filters, q });
          onSearch();
        })}
      />

      <div className="flex flex-wrap justify-center gap-2">
        {JOB_DOMAINS.map((d) => (
          <button
            key={d.id}
            type="button"
            onClick={() => toggleDomain(d.id)}
            className={cn(
              "rounded-full px-4 py-2 text-[12px] font-medium transition-all duration-300",
              filters.domains.includes(d.id)
                ? "bg-[#1d1d1f] text-white"
                : "text-[#6e6e73] hover:text-[#1d1d1f]"
            )}
          >
            {d.name}
          </button>
        ))}
      </div>

      <div className="max-w-md mx-auto space-y-6">
        <div>
          <p className="text-[12px] text-[#6e6e73] text-center mb-4">
            ₹{(filters.minCtc / 100000).toFixed(0)}L — ₹{(filters.maxCtc / 100000).toFixed(0)}L
          </p>
          <Slider
            min={CTC_MIN}
            max={CTC_MAX}
            step={100000}
            value={[filters.minCtc, filters.maxCtc]}
            onValueChange={([min, max]) => onChange({ ...filters, minCtc: min, maxCtc: max })}
            aria-label="CTC range filter"
          />
        </div>
        <Input
          id="location-filter"
          placeholder="Location"
          value={filters.location}
          onChange={(e) => onChange({ ...filters, location: e.target.value })}
          aria-label="Location filter"
        />
      </div>
    </div>
  );
}