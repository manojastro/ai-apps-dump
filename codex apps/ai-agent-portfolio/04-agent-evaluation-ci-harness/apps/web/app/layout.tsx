import Link from 'next/link';
import './globals.css';

export const metadata = { title: 'EvalHarness', description: 'Agent quality before deployment' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>
    <header><Link className="brand" href="/"><span>EH</span> EvalHarness</Link>
      <nav><Link href="/">Overview</Link><a href="/#runs">Experiments</a><a href="/#datasets">Datasets</a><a href="/#ci">CI gates</a></nav>
      <div className="status"><i /> Deterministic mode</div>
    </header>
    <main>{children}</main>
  </body></html>;
}
