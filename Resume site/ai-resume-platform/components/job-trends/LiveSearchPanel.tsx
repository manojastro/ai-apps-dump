"use client";

import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Copy, ExternalLink, Loader2, Search, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  liveSearch,
  LiveSearchClientError,
  type LiveSearchCitation,
  type LiveSearchResponse,
} from "@/lib/liveSearchClient";
import { listContainerVariants, listItemVariants, easeOutExpo } from "@/lib/motion";
import { useToastStore } from "@/store/toastStore";

const SUGGESTIONS = [
  "Cloud & DevOps hiring in India",
  "AI/ML skills in demand right now",
  "Fullstack interview prep in 2026",
];

function domainOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function renderAnswerWithCitations(
  answer: string,
  citations: LiveSearchCitation[],
  onCiteClick: (id: number) => void,
  highlightId: number | null
) {
  const byId = new Map(citations.map((c) => [c.id, c]));
  const parts = answer.split(/(\[\d+\])/g);

  return parts.map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    if (!m) {
      return (
        <span key={i} className="whitespace-pre-wrap">
          {part}
        </span>
      );
    }
    const id = Number(m[1]);
    const cite = byId.get(id);
    if (!cite?.url) {
      return (
        <span key={i} className="font-medium text-[#0071e3]">
          [{id}]
        </span>
      );
    }
    return (
      <button
        key={i}
        type="button"
        onClick={() => onCiteClick(id)}
        className={`font-medium text-[#0071e3] underline-offset-2 hover:underline ${
          highlightId === id ? "rounded bg-[#0071e3]/15 px-0.5" : ""
        }`}
        title={cite.title}
      >
        [{id}]
      </button>
    );
  });
}

export function LiveSearchPanel() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LiveSearchResponse | null>(null);
  const [lastQuery, setLastQuery] = useState("");
  const [highlightId, setHighlightId] = useState<number | null>(null);
  const citeRefs = useRef<Record<number, HTMLLIElement | null>>({});
  const addToast = useToastStore((s) => s.addToast);
  const reduce = useReducedMotion();

  const runSearch = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) {
      setError("Enter a question to search.");
      return;
    }
    if (trimmed.length > 1000) {
      setError("Query must be at most 1,000 characters.");
      return;
    }

    setLoading(true);
    setError(null);
    setLastQuery(trimmed);
    setHighlightId(null);

    try {
      const data = await liveSearch(trimmed);
      setResult(data);
    } catch (e) {
      setResult(null);
      if (e instanceof LiveSearchClientError) setError(e.message);
      else if (e instanceof Error) setError(e.message);
      else setError("Live search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const onCiteClick = (id: number) => {
    setHighlightId(id);
    citeRefs.current[id]?.scrollIntoView({
      behavior: reduce ? "auto" : "smooth",
      block: "nearest",
    });
    window.setTimeout(() => setHighlightId(null), 1600);
  };

  const copyAnswer = async () => {
    if (!result?.answer) return;
    try {
      await navigator.clipboard.writeText(result.answer);
      addToast("Answer copied", "success");
    } catch {
      addToast("Could not copy", "error");
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void runSearch(query);
  };

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-[20px] font-semibold tracking-tight text-[#1d1d1f]">
          Ask about the market
        </h2>
        <p className="mt-1 text-[14px] text-[#6e6e73]">
          Answers are built from current web pages and cite every source.
        </p>
      </div>

      <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Which cloud skills are in demand in India?"
          maxLength={1000}
          disabled={loading}
          aria-label="Live search query"
          className="flex-1 focus-ring"
        />
        <Button type="submit" disabled={loading} size="lg" className="shrink-0">
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              Search
            </>
          )}
        </Button>
      </form>

      {!result && !error && !loading && (
        <motion.div
          className="flex flex-wrap gap-2"
          variants={listContainerVariants}
          initial="hidden"
          animate="visible"
        >
          {SUGGESTIONS.map((s) => (
            <motion.button
              key={s}
              type="button"
              variants={listItemVariants}
              onClick={() => {
                setQuery(s);
                void runSearch(s);
              }}
              className="rounded-full bg-[#1d1d1f]/[0.04] px-3.5 py-1.5 text-[12px] text-[#6e6e73] transition-colors hover:bg-[#0071e3]/[0.08] hover:text-[#0071e3]"
            >
              {s}
            </motion.button>
          ))}
        </motion.div>
      )}

      {loading && (
        <p className="flex items-center gap-2 text-[13px] text-[#6e6e73]">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Reading current sources…
        </p>
      )}

      {error && !loading && (
        <div className="rounded-2xl border border-[#ff3b30]/15 bg-[#ff3b30]/[0.06] px-5 py-4">
          <p className="text-[13px] leading-relaxed text-[#6e6e73]">{error}</p>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="mt-3"
            onClick={() => void runSearch(lastQuery || query)}
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Retry
          </Button>
        </div>
      )}

      <AnimatePresence>
        {result && !loading && (
          <motion.div
            initial={reduce ? { opacity: 0 } : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: easeOutExpo }}
            className="premium-card-static space-y-5 px-6 py-6"
          >
            <div className="text-[15px] leading-relaxed text-[#1d1d1f]">
              {renderAnswerWithCitations(
                result.answer,
                result.citations,
                onCiteClick,
                highlightId
              )}
            </div>

            <Button type="button" variant="secondary" size="sm" onClick={copyAnswer}>
              <Copy className="h-3.5 w-3.5" />
              Copy answer
            </Button>

            {result.citations.length > 0 && (
              <div className="border-t border-black/[0.06] pt-4">
                <p className="section-label mb-3">Sources</p>
                <ol className="space-y-2.5">
                  {result.citations.map((c) => (
                    <li
                      key={c.id}
                      ref={(el) => {
                        citeRefs.current[c.id] = el;
                      }}
                      className={`flex gap-2 rounded-xl p-2 text-[13px] transition-colors ${
                        highlightId === c.id ? "bg-[#0071e3]/[0.08]" : ""
                      }`}
                    >
                      <span className="shrink-0 font-medium text-[#0071e3]">
                        [{c.id}]
                      </span>
                      <div className="min-w-0">
                        <a
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 break-words font-medium text-[#1d1d1f] hover:text-[#0071e3]"
                        >
                          {c.title}
                          <ExternalLink className="h-3 w-3 shrink-0 opacity-50" />
                        </a>
                        <p className="mt-0.5 text-[12px] text-[#6e6e73]">
                          {domainOf(c.url)}
                          {c.publishedDate ? ` · ${c.publishedDate}` : ""}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
