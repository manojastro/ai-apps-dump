import {
  addDays,
  differenceInCalendarDays,
  format,
  formatDistanceToNowStrict,
  isAfter,
  isBefore,
  parseISO,
  startOfDay,
  startOfWeek,
} from "date-fns";

export function parseDate(value?: string | null) {
  if (!value) return null;
  const d = parseISO(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** India has no DST; UTC+5:30 is the product timezone. */
export function nowInKolkata() {
  const now = new Date();
  const utc = now.getTime() + now.getTimezoneOffset() * 60_000;
  return new Date(utc + 5.5 * 3_600_000);
}

export function todayInTz() {
  return startOfDay(nowInKolkata());
}

export function isoDate(date: Date) {
  return format(date, "yyyy-MM-dd");
}

export function formatDate(value?: string | null, fallback = "—") {
  const d = parseDate(value);
  if (!d) return fallback;
  return format(d, "dd MMM yyyy");
}

export function formatDateTime(value?: string | null, fallback = "—") {
  const d = parseDate(value);
  if (!d) return fallback;
  return format(d, "dd MMM yyyy, HH:mm");
}

export function relativeToNow(value?: string | null) {
  const d = parseDate(value);
  if (!d) return "";
  return formatDistanceToNowStrict(d, { addSuffix: true });
}

export function isOverdue(value?: string | null) {
  const d = parseDate(value);
  if (!d) return false;
  return isBefore(startOfDay(d), todayInTz());
}

export function isDueToday(value?: string | null) {
  const d = parseDate(value);
  if (!d) return false;
  return isoDate(startOfDay(d)) === isoDate(todayInTz());
}

export function daysUntil(value?: string | null) {
  const d = parseDate(value);
  if (!d) return null;
  return differenceInCalendarDays(startOfDay(d), todayInTz());
}

export function weekStartIso(date = nowInKolkata()) {
  return isoDate(startOfWeek(date, { weekStartsOn: 1 }));
}

export function addDaysIso(value: string, days: number) {
  const d = parseDate(value);
  if (!d) return isoDate(addDays(nowInKolkata(), days));
  return isoDate(addDays(d, days));
}

export function isUpcoming(value?: string | null, withinDays = 7) {
  const d = parseDate(value);
  if (!d) return false;
  const now = todayInTz();
  return !isBefore(startOfDay(d), now) && !isAfter(startOfDay(d), addDays(now, withinDays));
}

export function inRange(iso: string, from?: string, to?: string) {
  const d = parseDate(iso);
  if (!d) return false;
  if (from) {
    const f = parseDate(from);
    if (f && isBefore(d, f)) return false;
  }
  if (to) {
    const t = parseDate(to);
    if (t && isAfter(d, t)) return false;
  }
  return true;
}
