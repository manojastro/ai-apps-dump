import Link from "next/link";
import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Signal Room · Incident RCA",
  description: "Evidence-grounded multi-agent incident investigations",
};

const nav = [
  ["Incidents", "/incidents"],
  ["Dependency graph", "/graph"],
  ["Evaluation", "/evaluation"],
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <aside>
          <Link className="brand" href="/incidents"><span>SR</span><div>Signal Room<small>INCIDENT INTELLIGENCE</small></div></Link>
          <nav>{nav.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}</nav>
          <div className="system-state"><i /> Evidence guard active<small>Deterministic mode</small></div>
        </aside>
        <main>{children}</main>
      </body>
    </html>
  );
}

