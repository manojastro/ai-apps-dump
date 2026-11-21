"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, FileText, TrendingUp } from "lucide-react";
import { AnimatedSection } from "@/components/shared/AnimatedSection";
import { listContainerVariants, listItemVariants, easeOutExpo } from "@/lib/motion";

const MODULES = [
  {
    href: "/resume-builder",
    icon: FileText,
    title: "Resume Builder",
    desc: "Paste, answer a few questions, or upload an old resume. Pick a template, download .docx.",
    cta: "Start building",
  },
  {
    href: "/job-trends",
    icon: TrendingUp,
    title: "Job Trends",
    desc: "See which domains are hiring, ask questions about the market, and browse open roles.",
    cta: "View trends",
  },
];

const VALUE_POINTS = [
  {
    title: "AI that doesn't invent",
    desc: "It rewrites and structures what you wrote — no fabricated jobs, dates, or metrics.",
  },
  {
    title: "ATS-safe by default",
    desc: "Single-column templates that resume parsers can read. Word (.docx) export.",
  },
  {
    title: "Answers with sources",
    desc: "Market questions come back with links you can open and check yourself.",
  },
];

export function LandingPage() {
  const reduce = useReducedMotion();

  return (
    <div className="pb-24">
      <section className="px-6 pb-14 pt-16 text-center md:pb-16 md:pt-24">
        <motion.div
          initial={reduce ? { opacity: 0 } : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: easeOutExpo }}
        >
          <h1 className="text-hero mx-auto max-w-3xl text-[#1d1d1f]">
            Land the role.
            <br />
            <span className="bg-gradient-to-r from-[#0071e3] to-[#5856d6] bg-clip-text text-transparent">
              Know the market.
            </span>
          </h1>
          <p className="text-hero-sub mx-auto mt-5 max-w-lg">
            Build an ATS-ready resume with AI and see what&rsquo;s hiring in
            India. No account — your draft stays in this browser.
          </p>

          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
            <Link
              href="/resume-builder"
              className="group inline-flex h-11 items-center gap-2 rounded-full bg-[#0071e3] px-7 text-[14px] font-medium text-white shadow-sm shadow-[#0071e3]/25 transition-colors duration-200 hover:bg-[#0077ed] focus-ring"
            >
              Create my resume
              <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/job-trends"
              className="inline-flex h-11 items-center rounded-full px-7 text-[14px] font-medium text-[#0071e3] transition-opacity hover:opacity-70 focus-ring"
            >
              Explore jobs
            </Link>
          </div>
        </motion.div>
      </section>

      <AnimatedSection className="mx-auto mb-20 max-w-5xl px-6">
        <div className="grid gap-5 md:grid-cols-2">
          {MODULES.map((card, i) => (
            <motion.div
              key={card.href}
              initial={reduce ? { opacity: 0 } : { opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.4, delay: i * 0.06, ease: easeOutExpo }}
            >
              <Link
                href={card.href}
                className="premium-card group block h-full p-8 focus-ring md:p-10"
              >
                <card.icon
                  className="mb-5 h-6 w-6 text-[#1d1d1f]"
                  strokeWidth={1.5}
                />
                <h2 className="mb-2 text-[24px] font-semibold tracking-tight text-[#1d1d1f]">
                  {card.title}
                </h2>
                <p className="mb-5 text-[15px] leading-relaxed text-[#6e6e73]">
                  {card.desc}
                </p>
                <span className="inline-flex items-center gap-1 text-[14px] font-medium text-[#0071e3] transition-all duration-300 group-hover:gap-2">
                  {card.cta} <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </Link>
            </motion.div>
          ))}
        </div>
      </AnimatedSection>

      <AnimatedSection className="mx-auto max-w-5xl px-6">
        <motion.div
          className="grid gap-8 border-t border-[#1d1d1f]/[0.06] pt-12 md:grid-cols-3"
          variants={listContainerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.2 }}
        >
          {VALUE_POINTS.map((f) => (
            <motion.div key={f.title} variants={listItemVariants}>
              <h3 className="mb-1.5 text-[15px] font-semibold text-[#1d1d1f]">
                {f.title}
              </h3>
              <p className="text-[14px] leading-relaxed text-[#6e6e73]">
                {f.desc}
              </p>
            </motion.div>
          ))}
        </motion.div>

        <p className="mt-10 text-[13px] leading-relaxed text-[#6e6e73]">
          Your resume is sent to the AI service only when you press Enhance.
          Nothing is stored on a server — drafts live in this browser until you
          clear them.
        </p>
      </AnimatedSection>
    </div>
  );
}
