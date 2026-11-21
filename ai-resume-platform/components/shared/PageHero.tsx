"use client";

import { motion } from "framer-motion";

interface PageHeroProps {
  title: string;
  subtitle: string;
}

export function PageHero({ title, subtitle }: PageHeroProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: [0.25, 0.1, 0.25, 1] }}
      className="text-center px-4 mb-16 md:mb-20"
    >
      <h1 className="text-hero text-[#1d1d1f]">{title}</h1>
      <p className="text-hero-sub mt-4 max-w-xl mx-auto">{subtitle}</p>
    </motion.div>
  );
}