// Decimal-string formatting without floating point. Input like "-2670.7" -> "(2,670.70)".

export function formatDecimal(value: string | null | undefined, places = 2, grouping: "intl" | "indian" = "intl"): string {
  if (value === null || value === undefined || value === "") return "—";
  const m = /^(-)?(\d*)(?:\.(\d*))?$/.exec(value.trim());
  if (!m) return value;
  const neg = m[1] === "-";
  let int = m[2] || "0";
  let frac = (m[3] ?? "").padEnd(places, "0");
  if (frac.length > places) {
    // round half-even on the string digits
    const keep = frac.slice(0, places);
    const rest = frac.slice(places);
    const roundUp = rest[0] > "5" || (rest[0] === "5" && (/[1-9]/.test(rest.slice(1)) || Number(keep.at(-1) ?? int.at(-1)) % 2 === 1));
    frac = keep;
    if (roundUp) {
      const digits = (int + frac).split("").map(Number);
      let i = digits.length - 1;
      while (i >= 0) {
        if (digits[i] === 9) { digits[i] = 0; i--; } else { digits[i]++; break; }
      }
      if (i < 0) digits.unshift(1);
      const s = digits.join("");
      int = s.slice(0, s.length - places) || "0";
      frac = places ? s.slice(s.length - places) : "";
    }
  }
  const grouped = grouping === "indian" ? groupIndian(int) : int.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const out = places > 0 ? `${grouped}.${frac}` : grouped;
  const isZero = /^[0,.]*$/.test(out);
  return neg && !isZero ? `(${out})` : out;
}

function groupIndian(int: string): string {
  if (int.length <= 3) return int;
  const tail = int.slice(-3);
  let head = int.slice(0, -3);
  const parts: string[] = [];
  while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
  if (head) parts.unshift(head);
  return `${parts.join(",")},${tail}`;
}

export function formatRatio(value: string | null, unit: string | null): string {
  if (value === null) return "—";
  if (unit === "percent") {
    // value is a fraction: move the decimal point two places using string arithmetic
    const neg = value.startsWith("-");
    const [i, f = ""] = value.replace("-", "").split(".");
    const padded = f.padEnd(2, "0");
    const shifted = `${(i + padded.slice(0, 2)).replace(/^0+(?=\d)/, "")}.${padded.slice(2) || "0"}`;
    return `${neg ? "-" : ""}${formatDecimal(shifted, 1)}%`;
  }
  if (unit === "monetary") return formatDecimal(value, 0);
  return `${formatDecimal(value, 2)}x`;
}

export const SCALE_LABEL: Record<string, string> = {
  units: "", thousands: "thousand", lakhs: "lakh", crores: "crore", millions: "million", billions: "billion",
};
