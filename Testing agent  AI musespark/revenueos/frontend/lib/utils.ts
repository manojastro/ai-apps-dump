import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function formatMoney(value: number | null | undefined) {
  return value === null || value === undefined ? "-" : money.format(value);
}

export function formatCompact(value: number | null | undefined) {
  if (value === null || value === undefined) return "-";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return money.format(value);
}

export function formatPercent(value: number | null | undefined, digits = 0) {
  if (value === null || value === undefined) return "-";
  const text = (value * 100).toFixed(digits);
  return `${Number(text) === 0 ? (0).toFixed(digits) : text}%`;
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "-";
  return new Date(`${value.slice(0, 10)}T00:00:00`).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function titleCase(value: string | null | undefined) {
  if (!value) return "-";
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
