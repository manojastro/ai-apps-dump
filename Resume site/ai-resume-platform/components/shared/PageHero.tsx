"use client";

import { cn } from "@/lib/utils";

interface PageHeroProps {
  title: string;
  subtitle: string;
  className?: string;
}

/** Compact page header — keeps the tool itself above the fold. */
export function PageHero({ title, subtitle, className }: PageHeroProps) {
  return (
    <div className={cn("mb-10", className)}>
      <h1 className="page-title text-[#1d1d1f]">{title}</h1>
      <p className="mt-2 max-w-xl text-[15px] leading-relaxed text-[#6e6e73]">
        {subtitle}
      </p>
    </div>
  );
}
