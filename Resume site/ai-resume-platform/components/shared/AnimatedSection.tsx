"use client";

import { motion, useReducedMotion } from "framer-motion";
import { sectionVariants, fadeOnly } from "@/lib/motion";
import { cn } from "@/lib/utils";

interface AnimatedSectionProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  once?: boolean;
}

export function AnimatedSection({
  children,
  className,
  delay = 0,
  once = true,
}: AnimatedSectionProps) {
  const reduce = useReducedMotion();
  return (
    <motion.section
      className={cn(className)}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: 0.18 }}
      variants={reduce ? fadeOnly : sectionVariants}
      transition={reduce ? { duration: 0.15 } : { delay }}
    >
      {children}
    </motion.section>
  );
}
