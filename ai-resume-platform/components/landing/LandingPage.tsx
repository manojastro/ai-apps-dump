"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, FileText, TrendingUp, Sparkles, Shield, Zap } from "lucide-react";

const features = [
  {
    icon: Sparkles,
    title: "AI-enhanced",
    desc: "Gemini structures and rewrites your content without inventing experience.",
  },
  {
    icon: Shield,
    title: "ATS-safe",
    desc: "Single-column templates parsers love. Export as .docx, not PDF.",
  },
  {
    icon: Zap,
    title: "Live market data",
    desc: "Real openings and CTC from Adzuna — never LLM-guessed numbers.",
  },
];

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
};

export function LandingPage() {
  return (
    <div className="pb-24">
      {/* Hero */}
      <section className="text-center px-6 pt-16 md:pt-24 pb-20">
        <motion.div
          {...fadeUp}
          transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <p className="text-[12px] font-medium tracking-widest uppercase text-[#0071e3] mb-6">
            For Indian job seekers
          </p>
          <h1 className="text-hero text-[#1d1d1f] max-w-3xl mx-auto">
            Land the role.
            <br />
            <span className="bg-gradient-to-r from-[#0071e3] via-[#5856d6] to-[#0071e3] bg-clip-text text-transparent bg-[length:200%_auto] animate-[gradient_4s_ease_infinite]">
              Know the market.
            </span>
          </h1>
          <p className="text-hero-sub mt-6 max-w-lg mx-auto">
            Build an ATS-ready resume with AI. Explore real-time job trends across India.
          </p>
        </motion.div>

        <motion.div
          {...fadeUp}
          transition={{ duration: 0.8, delay: 0.15 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10"
        >
          <Link
            href="/resume-builder"
            className="inline-flex items-center gap-2 h-11 px-7 rounded-full bg-[#0071e3] text-white text-[14px] font-medium hover:bg-[#0077ed] transition-all duration-300 active:scale-[0.97]"
          >
            Build resume <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/job-trends"
            className="inline-flex items-center gap-2 h-11 px-7 rounded-full text-[#0071e3] text-[14px] font-medium hover:opacity-60 transition-opacity"
          >
            Explore jobs
          </Link>
        </motion.div>
      </section>

      {/* Product cards */}
      <section className="mx-auto max-w-5xl px-6 grid md:grid-cols-2 gap-6 mb-24">
        {[
          {
            href: "/resume-builder",
            icon: FileText,
            title: "Resume Builder",
            desc: "Paste, chat, or upload. Pick a template. Download .docx.",
            cta: "Start building",
            gradient: "from-[#0071e3]/5 to-transparent",
          },
          {
            href: "/job-trends",
            icon: TrendingUp,
            title: "Job Trends",
            desc: "Trending domains, CTC ranges, and filtered search across India.",
            cta: "View trends",
            gradient: "from-[#5856d6]/5 to-transparent",
          },
        ].map((card, i) => (
          <motion.div
            key={card.href}
            {...fadeUp}
            transition={{ duration: 0.7, delay: 0.2 + i * 0.1 }}
          >
            <Link
              href={card.href}
              className="group block rounded-3xl bg-white p-8 md:p-10 shadow-[0_2px_20px_rgba(0,0,0,0.06)] hover:shadow-[0_8px_40px_rgba(0,0,0,0.1)] transition-all duration-500 relative overflow-hidden"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
              <div className="relative">
                <card.icon className="h-6 w-6 text-[#1d1d1f] mb-6" strokeWidth={1.5} />
                <h2 className="text-[28px] font-semibold text-[#1d1d1f] tracking-tight mb-2">
                  {card.title}
                </h2>
                <p className="text-[15px] text-[#6e6e73] leading-relaxed mb-6">
                  {card.desc}
                </p>
                <span className="inline-flex items-center gap-1 text-[14px] text-[#0071e3] font-medium group-hover:gap-2 transition-all duration-300">
                  {card.cta} <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </div>
            </Link>
          </motion.div>
        ))}
      </section>

      {/* Features */}
      <section className="mx-auto max-w-5xl px-6">
        <p className="section-label text-center mb-10">Why ResumeAI</p>
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              {...fadeUp}
              transition={{ duration: 0.6, delay: 0.3 + i * 0.08 }}
              className="text-center"
            >
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#1d1d1f]/[0.04]">
                <f.icon className="h-5 w-5 text-[#1d1d1f]" strokeWidth={1.5} />
              </div>
              <h3 className="text-[17px] font-semibold text-[#1d1d1f] mb-2">{f.title}</h3>
              <p className="text-[14px] text-[#6e6e73] leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA band */}
      <section className="mx-auto max-w-5xl px-6 mt-24">
        <motion.div
          {...fadeUp}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="rounded-3xl bg-[#1d1d1f] p-10 md:p-14 text-center"
        >
          <h2 className="text-[28px] md:text-[36px] font-semibold text-white tracking-tight">
            Ready when you are.
          </h2>
          <p className="text-[15px] text-white/50 mt-3 mb-8">
            No account needed. Your work saves locally in this browser.
          </p>
          <Link
            href="/resume-builder"
            className="inline-flex items-center gap-2 h-11 px-7 rounded-full bg-white text-[#1d1d1f] text-[14px] font-medium hover:bg-white/90 transition-colors"
          >
            Get started <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </section>
    </div>
  );
}