"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

interface ModuleBridgeProps {
  title: string;
  description: string;
  href: string;
  cta: string;
}

export function ModuleBridge({ title, description, href, cta }: ModuleBridgeProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6 }}
      className="mt-20 rounded-2xl bg-[#1d1d1f]/[0.03] p-8 md:p-10 flex flex-col md:flex-row items-center justify-between gap-6"
    >
      <div className="text-center md:text-left">
        <p className="text-[17px] font-semibold text-[#1d1d1f] tracking-tight">{title}</p>
        <p className="text-[14px] text-[#6e6e73] mt-1">{description}</p>
      </div>
      <Link
        href={href}
        className="inline-flex items-center gap-2 text-[14px] text-[#0071e3] font-medium hover:gap-3 transition-all duration-300 shrink-0"
      >
        {cta} <ArrowRight className="h-4 w-4" />
      </Link>
    </motion.div>
  );
}