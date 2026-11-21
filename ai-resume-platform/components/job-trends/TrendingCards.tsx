"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { CountUp } from "./CountUp";
import type { TrendingDomainData } from "@/lib/adzuna";

export function TrendingCards() {
  const [domains, setDomains] = useState<TrendingDomainData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [isMock, setIsMock] = useState(false);

  const fetchTrending = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/jobs/trending");
      if (!res.ok) throw new Error("Failed to load trends");
      const data: TrendingDomainData[] = await res.json();
      setDomains(data);
      setIsMock(data.every((d) => d.openingCount === 0));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error loading trends");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTrending(); }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-36 rounded-2xl" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-center text-[15px] text-[#6e6e73]">
        {error}.{" "}
        <button onClick={fetchTrending} className="text-[#0071e3] hover:opacity-60">
          Retry
        </button>
      </p>
    );
  }

  if (domains.length === 0) {
    return (
      <p className="text-center text-[15px] text-[#6e6e73]">
        No trending data available.
      </p>
    );
  }

  return (
    <div>
      <p className="section-label text-center mb-4">Trending</p>
      {isMock && (
        <p className="text-center text-[12px] text-[#ff9500] mb-6">
          Live counts unavailable — add Adzuna API keys to .env.local and restart the server
        </p>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[#1d1d1f]/[0.06] rounded-2xl overflow-hidden">
        {domains.slice(0, 8).map((d, i) => (
          <motion.div
            key={d.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.05, duration: 0.5 }}
            onMouseEnter={() => setHovered(d.id)}
            onMouseLeave={() => setHovered(null)}
            className="bg-[#fbfbfd] p-6 md:p-8 relative group hover:bg-white transition-colors duration-500"
          >
            <div className="flex items-start justify-between mb-4">
              <p className="text-[40px] md:text-[48px] font-semibold text-[#1d1d1f] tracking-tighter leading-none">
                {isMock ? "—" : <CountUp end={d.openingCount} />}
              </p>
              {!isMock && d.trendDirection === "up" && (
                <TrendingUp className="h-3.5 w-3.5 text-[#34c759] opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </div>
            <p className="text-[13px] text-[#1d1d1f] font-medium leading-snug">{d.name}</p>
            <p className="text-[11px] text-[#6e6e73]/60 mt-1">{d.ctcDisplay}</p>

            {!isMock && (
              <motion.div
                initial={false}
                animate={{ opacity: hovered === d.id ? 1 : 0, y: hovered === d.id ? 0 : 4 }}
                className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-white via-white/95 to-transparent"
              >
                <p className="text-[11px] text-[#6e6e73] leading-relaxed line-clamp-2">
                  {d.blurb}
                </p>
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}