import type { PersonalInfo, TemplateStyleTokens } from "@/lib/resumeSchema";

export function formatContact(info: PersonalInfo, sep = " | "): string {
  return [
    info.email,
    info.phone,
    info.location,
    info.linkedin,
    info.portfolio,
  ]
    .filter(Boolean)
    .join(sep);
}

export function formatDateRange(
  start: string,
  end: string,
  current: boolean
): string {
  if (!start && !end) return "";
  return current ? `${start} – Present` : `${start} – ${end}`;
}

interface SectionProps {
  title: string;
  style: TemplateStyleTokens;
  variant?: "blue" | "bw" | "ats" | "minimal" | "tech";
  children: React.ReactNode;
}

export function Section({ title, style, variant = "blue", children }: SectionProps) {
  const headingStyles: Record<string, string> = {
    blue: `font-bold uppercase tracking-wider text-sm border-b-2 pb-1 mb-3`,
    bw: `font-bold uppercase tracking-widest text-xs border-b border-black pb-1 mb-3`,
    ats: `font-bold uppercase text-sm border-b border-black pb-0.5 mb-2`,
    minimal: `font-medium uppercase tracking-widest text-xs mb-3`,
    tech: `font-bold uppercase text-xs tracking-wider border-l-4 pl-2 mb-3`,
  };

  return (
    <div style={{ marginBottom: style.sectionSpacing }}>
      <h2
        className={headingStyles[variant]}
        style={{
          color: variant === "minimal" ? style.mutedColor : style.accentColor,
          borderColor: style.accentColor,
        }}
      >
        {title}
      </h2>
      {children}
    </div>
  );
}

export function BulletList({
  items,
  style,
}: {
  items: string[];
  style: TemplateStyleTokens;
}) {
  const bullet = style.bulletStyle === "dash" ? "–" : "•";
  return (
    <ul className="space-y-1">
      {items.filter(Boolean).map((b, i) => (
        <li
          key={i}
          className="text-sm pl-4 relative leading-relaxed"
          style={{ color: style.textColor }}
        >
          <span
            className="absolute left-0"
            style={{ color: style.mutedColor }}
          >
            {bullet}
          </span>
          {b}
        </li>
      ))}
    </ul>
  );
}