"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/resume-builder", label: "Resume" },
  { href: "/job-trends", label: "Jobs" },
];

export function Navbar() {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <header className="sticky top-0 z-50 glass-nav">
      <div className="mx-auto flex h-12 max-w-5xl items-center justify-between px-6">
        <Link
          href="/"
          className={cn(
            "text-[14px] font-semibold tracking-tight transition-opacity duration-300",
            isHome ? "text-[#1d1d1f]" : "text-[#1d1d1f] opacity-90 hover:opacity-60"
          )}
        >
          ResumeAI
        </Link>

        <nav className="flex items-center gap-8" aria-label="Main navigation">
          {links.map(({ href, label }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "text-[12px] font-medium tracking-wide transition-opacity duration-300",
                  active
                    ? "text-[#1d1d1f] opacity-100"
                    : "text-[#1d1d1f] opacity-40 hover:opacity-70"
                )}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}