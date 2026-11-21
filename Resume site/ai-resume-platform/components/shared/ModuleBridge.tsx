"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface ModuleBridgeProps {
  title: string;
  description: string;
  href: string;
  cta: string;
}

export function ModuleBridge({ title, description, href, cta }: ModuleBridgeProps) {
  return (
    <div className="mt-16 flex flex-col items-start justify-between gap-4 border-t border-[#1d1d1f]/[0.06] pt-8 sm:flex-row sm:items-center">
      <div>
        <p className="text-[15px] font-semibold tracking-tight text-[#1d1d1f]">
          {title}
        </p>
        <p className="mt-0.5 text-[14px] text-[#6e6e73]">{description}</p>
      </div>
      <Link
        href={href}
        className="inline-flex shrink-0 items-center gap-1.5 text-[14px] font-medium text-[#0071e3] transition-all duration-300 hover:gap-2.5"
      >
        {cta} <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}
