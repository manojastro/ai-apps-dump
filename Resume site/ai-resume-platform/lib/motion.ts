/**
 * Shared Framer Motion presets — premium, controlled, Apple/SaaS-like.
 * Prefer opacity + transform. Respect prefers-reduced-motion.
 */

import type { Transition, Variants } from "framer-motion";

export const easeOutExpo: [number, number, number, number] = [0.16, 1, 0.3, 1];
export const easeOutSoft: [number, number, number, number] = [0.25, 0.1, 0.25, 1];

export const pageTransition: Transition = {
  duration: 0.32,
  ease: easeOutExpo,
};

export const pageVariants: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

export const sectionVariants: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: easeOutExpo },
  },
};

export const cardVariants: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: easeOutExpo },
  },
};

export const listContainerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.045, delayChildren: 0.04 },
  },
};

export const listItemVariants: Variants = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: easeOutExpo },
  },
};

export const toastVariants: Variants = {
  initial: { opacity: 0, y: 14, scale: 0.98 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.28, ease: easeOutExpo },
  },
  exit: {
    opacity: 0,
    y: 8,
    scale: 0.98,
    transition: { duration: 0.18 },
  },
};

export const modalVariants: Variants = {
  initial: { opacity: 0, scale: 0.98, y: 8 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: 0.28, ease: easeOutExpo },
  },
  exit: {
    opacity: 0,
    scale: 0.98,
    y: 6,
    transition: { duration: 0.18 },
  },
};

export const fadeOnly: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.22 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

export const slideDir = (dir: 1 | -1): Variants => ({
  initial: { opacity: 0, x: dir * 16 },
  animate: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.28, ease: easeOutExpo },
  },
  exit: {
    opacity: 0,
    x: dir * -12,
    transition: { duration: 0.2 },
  },
});

/** Reduced-motion safe variants (short fades only). */
export const reducedPageVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export function getPageVariants(reduceMotion: boolean): Variants {
  return reduceMotion ? reducedPageVariants : pageVariants;
}

export function getPageTransition(reduceMotion: boolean): Transition {
  return reduceMotion
    ? { duration: 0.15 }
    : pageTransition;
}
