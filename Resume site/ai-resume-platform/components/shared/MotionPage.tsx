"use client";

import { motion, useReducedMotion } from "framer-motion";
import { getPageTransition, getPageVariants } from "@/lib/motion";
import { cn } from "@/lib/utils";

interface MotionPageProps {
  children: React.ReactNode;
  className?: string;
}

export function MotionPage({ children, className }: MotionPageProps) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial="initial"
      animate="animate"
      exit="exit"
      variants={getPageVariants(!!reduce)}
      transition={getPageTransition(!!reduce)}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
