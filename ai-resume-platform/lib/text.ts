export function cleanText(value: string): string {
  return value
    .replace(/\u0000/g, "")
    .replace(/\r\n?/g, "\n")
    .replace(/[\u0001-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, "")
    .trim();
}

export function oneLine(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

export function normalizeUrl(value: string): string | null {
  const raw = value.trim();
  if (!raw) return null;

  let candidate = raw;
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(candidate)) {
    return `mailto:${candidate}`;
  }
  if (!/^[a-z][a-z0-9+.-]*:/i.test(candidate)) {
    candidate = `https://${candidate}`;
  }

  try {
    const url = new URL(candidate);
    if (!["http:", "https:", "mailto:", "tel:"].includes(url.protocol)) {
      return null;
    }
    return url.toString();
  } catch {
    return null;
  }
}

export function normalizeWebUrl(value: string): string | null {
  const href = normalizeUrl(value);
  if (!href) return null;
  try {
    const url = new URL(href);
    if (!["http:", "https:"].includes(url.protocol)) return null;
    return url.toString();
  } catch {
    return null;
  }
}

export function displayUrl(value: string): string {
  return value
    .replace(/^https?:\/\//i, "")
    .replace(/^www\./i, "")
    .replace(/\/$/, "");
}

export function filenameForResume(name: string): string {
  const base = name
    .normalize("NFKD")
    .replace(/[^\x00-\x7F]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return `${base || "Resume"}_Resume.pdf`;
}

export function extractNumbers(value: string): string[] {
  return (value.match(/\d+(?:[.,]\d+)?%?/g) ?? []).map((item) =>
    item.replace(",", "")
  );
}

export function includesInsensitive(haystack: string, needle: string): boolean {
  const normalizedNeedle = needle.trim().toLowerCase();
  if (!normalizedNeedle) return false;
  return haystack.toLowerCase().includes(normalizedNeedle);
}

export function uniqueBy<T>(items: T[], key: (item: T) => string): T[] {
  const seen = new Set<string>();
  const result: T[] = [];
  for (const item of items) {
    const value = key(item).trim().toLowerCase();
    if (!value || seen.has(value)) continue;
    seen.add(value);
    result.push(item);
  }
  return result;
}

export function splitLines(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((line) => line.replace(/\s+$/g, "").trim())
    .filter((line, index, all) => line.length > 0 || all[index - 1]?.length);
}

export function stripBullet(value: string): string {
  return value
    .replace(/^\s*(?:[•▪◦‣●○·*+\-–—]|\d{1,2}[.)])\s+/, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function stripTrailingPunctuation(value: string): string {
  return value.replace(/[;,.]+$/g, "").trim();
}

export function titleCaseIfShouting(value: string): string {
  if (value.length < 3) return value;
  const letters = value.replace(/[^a-z]/gi, "");
  if (!letters) return value;
  const uppercase = value.replace(/[^A-Z]/g, "").length;
  if (uppercase / letters.length < 0.85) return value;
  return value
    .toLowerCase()
    .replace(/\b([a-z])/g, (letter) => letter.toUpperCase());
}

const MONTHS: Record<string, string> = {
  jan: "01",
  january: "01",
  feb: "02",
  february: "02",
  mar: "03",
  march: "03",
  apr: "04",
  april: "04",
  may: "05",
  jun: "06",
  june: "06",
  jul: "07",
  july: "07",
  aug: "08",
  august: "08",
  sep: "09",
  sept: "09",
  september: "09",
  oct: "10",
  october: "10",
  nov: "11",
  november: "11",
  dec: "12",
  december: "12",
};

const DATE_TOKEN =
  "(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\\.?\\s+\\d{2,4}|\\d{1,2}\\/\\d{2,4}|\\d{4}";
const DATE_END =
  "(?:Present|Current|Now|Present\\s*\\(\\s*ongoing\\s*\\)|Ongoing|Till\\s+date|To\\s+date)";

export const DATE_RANGE_RE = new RegExp(
  `(${DATE_TOKEN})\\s*(?:-|–|—|to|until)\\s*(${DATE_END}|${DATE_TOKEN})`,
  "i"
);

export function isPresentDate(value: string): boolean {
  return /present|current|now|ongoing|till\s+date|to\s+date/i.test(value);
}

export function normalizeYearMonth(value: string): string | null {
  const text = value.trim().toLowerCase().replace(/\./g, "");
  const monthYear = text.match(
    /^(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{2,4})$/
  );
  if (monthYear) {
    const month = MONTHS[monthYear[1]];
    let year = monthYear[2];
    if (year.length === 2) year = `20${year}`;
    return `${year}-${month}`;
  }
  const numeric = text.match(/^(\d{1,2})\/(\d{2,4})$/);
  if (numeric) {
    const month = numeric[1].padStart(2, "0");
    let year = numeric[2];
    if (year.length === 2) year = `20${year}`;
    return `${year}-${month}`;
  }
  const year = text.match(/^(\d{4})$/);
  if (year) return year[1];
  return null;
}

export function readableDate(value: string): string {
  const raw = value.trim();
  if (!raw) return "";
  if (isPresentDate(raw)) return raw;
  const normalized = normalizeYearMonth(raw);
  if (!normalized) return raw;
  if (/^\d{4}$/.test(normalized)) return normalized;
  const [year, month] = normalized.split("-");
  const monthName = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ][Number(month) - 1];
  return monthName ? `${monthName} ${year}` : raw;
}
