"use client";

import { useEffect, useState } from "react";
import { Clock } from "lucide-react";

const STORAGE_KEY = "resumeai-recent-searches";
const MAX = 5;

export function getRecentSearches(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

export function addRecentSearch(query: string) {
  if (!query.trim() || typeof window === "undefined") return;
  const recent = getRecentSearches().filter((s) => s !== query);
  recent.unshift(query);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(recent.slice(0, MAX)));
}

interface RecentSearchesProps {
  onSelect: (query: string) => void;
}

export function RecentSearches({ onSelect }: RecentSearchesProps) {
  const [searches, setSearches] = useState<string[]>([]);

  useEffect(() => {
    setSearches(getRecentSearches());
  }, []);

  if (searches.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center justify-center gap-2">
      <Clock className="h-3 w-3 text-[#6e6e73]/50" />
      {searches.map((s) => (
        <button
          key={s}
          onClick={() => onSelect(s)}
          className="text-[12px] text-[#6e6e73] hover:text-[#0071e3] transition-colors"
        >
          {s}
        </button>
      ))}
    </div>
  );
}