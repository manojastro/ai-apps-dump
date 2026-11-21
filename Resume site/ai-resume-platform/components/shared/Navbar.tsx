"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

const links = [
  { href: "/resume-builder", label: "Resume" },
  { href: "/job-trends", label: "Jobs" },
];

export function Navbar() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const reduce = useReducedMotion();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  return (
    <header className={cn("sticky top-0 z-50 glass-nav", scrolled && "scrolled")}>
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
        <Link
          href="/"
          className="flex items-center gap-2.5 rounded-lg text-[15px] font-semibold tracking-tight text-[#1d1d1f] focus-ring"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-gradient-to-br from-[#0071e3] to-[#5856d6] text-[11px] font-bold text-white">
            R
          </span>
          ResumeAI
        </Link>

        <nav className="hidden items-center gap-1 sm:flex" aria-label="Main navigation">
          {links.map(({ href, label }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors focus-ring",
                  active ? "text-[#1d1d1f]" : "text-[#6e6e73] hover:text-[#1d1d1f]"
                )}
              >
                {active &&
                  (reduce ? (
                    <span className="absolute inset-0 rounded-full bg-[#1d1d1f]/[0.06]" />
                  ) : (
                    <motion.span
                      layoutId="nav-active-pill"
                      className="absolute inset-0 rounded-full bg-[#1d1d1f]/[0.06]"
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                    />
                  ))}
                <span className="relative z-10">{label}</span>
              </Link>
            );
          })}
        </nav>

        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1d1d1f]/[0.05] focus-ring sm:hidden"
          aria-expanded={mobileOpen}
          aria-label="Menu"
          onClick={() => setMobileOpen((v) => !v)}
        >
          <div className="flex w-4 flex-col gap-1">
            <span
              className={cn(
                "h-0.5 rounded-full bg-[#1d1d1f] transition-transform duration-200",
                mobileOpen && "translate-y-[3px] rotate-45"
              )}
            />
            <span
              className={cn(
                "h-0.5 rounded-full bg-[#1d1d1f] transition-opacity duration-200",
                mobileOpen && "opacity-0"
              )}
            />
            <span
              className={cn(
                "h-0.5 rounded-full bg-[#1d1d1f] transition-transform duration-200",
                mobileOpen && "-translate-y-[3px] -rotate-45"
              )}
            />
          </div>
        </button>
      </div>

      {mobileOpen && (
        <div className="border-t border-black/[0.04] bg-white/95 px-6 py-3 backdrop-blur-xl sm:hidden">
          <div className="flex flex-col gap-1">
            {links.map(({ href, label }) => {
              const active = pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "rounded-xl px-3 py-2.5 text-[14px] font-medium",
                    active ? "bg-[#0071e3]/10 text-[#0071e3]" : "text-[#1d1d1f]"
                  )}
                >
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}
