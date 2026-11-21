"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";
import { CountUp } from "./CountUp";
import type { TrendingDomainData } from "@/lib/adzuna";

interface TrendingApiResponse {
  domains?: TrendingDomainData[];
  source?: "adzuna" | "exa" | "mock";
  note?: string;
  detail?: string;
}

/** Maps a machine failure code to one honest, vendor-free sentence. */
function synthesisReason(detail?: string): string {
  switch (detail) {
    case "auth_error":
      return " The research service rejected its credentials.";
    case "rate_limit":
      return " The research service is rate-limited right now.";
    case "timeout":
      return " The research service timed out.";
    case "empty_or_unparseable":
      return " The research summary could not be read.";
    default:
      return "";
  }
}

function signalLabel(signal?: string): string {
  switch (signal) {
    case "strong":
      return "Strong demand";
    case "moderate":
      return "Moderate demand";
    case "limited":
      return "Limited demand";
    default:
      return "No signal";
  }
}

function signalColor(signal?: string): string {
  switch (signal) {
    case "strong":
      return "text-[#248a3d]";
    case "moderate":
      return "text-[#0071e3]";
    default:
      return "text-[#6e6e73]";
  }
}

export function TrendingCards() {
  const [domains, setDomains] = useState<TrendingDomainData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<"adzuna" | "exa" | "mock">("mock");
  const [note, setNote] = useState<string>("");
  const [detail, setDetail] = useState<string>("");

  const fetchTrending = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/jobs/trending");
      if (!res.ok) throw new Error("Failed to load trends");
      const data = (await res.json()) as TrendingDomainData[] | TrendingApiResponse;

      if (Array.isArray(data)) {
        setDomains(data);
        setSource(data.every((d) => d.openingCount === 0) ? "mock" : "adzuna");
        setNote("");
        setDetail("");
      } else {
        setDomains(data.domains ?? []);
        setSource(data.source ?? "mock");
        setNote(data.note ?? "");
        setDetail(typeof data.detail === "string" ? data.detail : "");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error loading trends");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrending();
  }, []);

  const header = (
    <div className="mb-5">
      <h2 className="text-[20px] font-semibold tracking-tight text-[#1d1d1f]">
        Where hiring is happening
      </h2>
      <p className="mt-1 text-[14px] text-[#6e6e73]">
        {note ||
          (source === "adzuna"
            ? "Live vacancy counts and salary ranges from Adzuna India."
            : "Demand signals from current web sources — not official vacancy counts.")}
      </p>
    </div>
  );

  if (loading) {
    return (
      <div>
        {header}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        {header}
        <p className="text-[14px] text-[#6e6e73]">
          {error}.{" "}
          <button
            onClick={fetchTrending}
            className="font-medium text-[#0071e3] hover:opacity-60"
          >
            Retry
          </button>
        </p>
      </div>
    );
  }

  if (domains.length === 0) {
    return (
      <div>
        {header}
        <p className="text-[14px] text-[#6e6e73]">No trending data available.</p>
      </div>
    );
  }

  const isAdzuna = source === "adzuna";

  // Without Adzuna counts, a card is only meaningful if web research actually
  // returned something. Otherwise every domain shows an identical default
  // signal, which would read as a finding rather than "no data".
  const hasResearch = domains.some(
    (d) => d.blurb?.trim() || (d.keySkills?.length ?? 0) > 0
  );

  if (!isAdzuna && !hasResearch) {
    return (
      <section>
        {header}
        <p className="text-[14px] leading-relaxed text-[#6e6e73]">
          No demand signals came back for these domains right now.
          {synthesisReason(detail)} Ask a specific question below to research
          the market directly.{" "}
          <button
            onClick={fetchTrending}
            className="font-medium text-[#0071e3] hover:opacity-60"
          >
            Retry
          </button>
        </p>
      </section>
    );
  }

  return (
    <section>
      {header}
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl bg-[#1d1d1f]/[0.06] md:grid-cols-4">
        {domains.slice(0, 8).map((d, i) => (
          <motion.div
            key={d.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.04, duration: 0.4 }}
            className="bg-[#fbfbfd] p-5"
          >
            {isAdzuna ? (
              <p className="text-[32px] font-semibold leading-none tracking-tighter text-[#1d1d1f]">
                <CountUp end={d.openingCount} />
              </p>
            ) : (
              <p
                className={`text-[15px] font-semibold leading-none tracking-tight ${signalColor(d.signal)}`}
              >
                {signalLabel(d.signal)}
              </p>
            )}
            <p className="mt-2.5 text-[13px] font-medium leading-snug text-[#1d1d1f]">
              {d.name}
            </p>
            {isAdzuna
              ? d.ctcDisplay && (
                  <p className="mt-0.5 text-[11px] text-[#6e6e73]">
                    {d.ctcDisplay}
                  </p>
                )
              : d.keySkills &&
                d.keySkills.length > 0 && (
                  <p className="mt-0.5 text-[11px] text-[#6e6e73]">
                    {d.keySkills.slice(0, 3).join(" · ")}
                  </p>
                )}
            {d.blurb && (
              <p className="mt-2 line-clamp-3 text-[11px] leading-relaxed text-[#6e6e73]">
                {d.blurb}
              </p>
            )}
          </motion.div>
        ))}
      </div>
    </section>
  );
}
