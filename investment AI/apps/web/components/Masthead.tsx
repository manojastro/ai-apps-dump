import Link from "next/link";

const links = [
  ["Onboarding", "/onboarding"],
  ["Holdings", "/holdings"],
  ["Research", "/research"],
  ["War room", "/war-room"],
  ["Compare", "/compare"],
  ["Sources", "/sources"],
];

export function Masthead() {
  return (
    <header className="border-b border-rule bg-navy-deep text-paper">
      <div className="mx-auto flex max-w-6xl flex-wrap items-end justify-between gap-4 px-5 py-4">
        <Link href="/" className="block">
          <div className="font-display text-2xl tracking-tight text-raised">Aegis Plan India</div>
          <p className="mt-1 max-w-md text-sm text-paper/80">
            Educational research desk — not a broker, not a SEBI-registered adviser.
          </p>
        </Link>
        <nav className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-paper/90">
          {links.map(([label, href]) => (
            <Link key={href} href={href} className="hover:text-brass">
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
