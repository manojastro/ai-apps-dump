import { DEFAULT_LOCALE } from "./constants";

export function formatLpa(value?: number | null, privacy = false) {
  if (privacy) return "₹•• LPA";
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  const formatted = new Intl.NumberFormat(DEFAULT_LOCALE, {
    maximumFractionDigits: value % 1 === 0 ? 0 : 1,
  }).format(value);
  return `₹${formatted} LPA`;
}

export function formatInr(value?: number | null, privacy = false) {
  if (privacy) return "₹••••";
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat(DEFAULT_LOCALE, {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function maskText(value: string | undefined, privacy: boolean, kind: "salary" | "contact" | "note" | "name" = "note") {
  if (!privacy || !value) return value ?? "";
  if (kind === "salary") return "••••";
  if (kind === "contact") return "Hidden in Privacy Mode";
  if (kind === "name") return "Referral hidden";
  return "Private note hidden";
}
