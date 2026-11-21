import Link from "next/link";
import { DISCLAIMER, NO_EXECUTION } from "@/lib/disclaimer";

export default function HomePage() {
  return (
    <div className="grid gap-10 lg:grid-cols-[1.3fr_0.7fr]">
      <article>
        <p className="text-brass">India-focused educational simulation</p>
        <h1 className="mt-3 font-display text-4xl leading-tight text-navy md:text-5xl">
          Research Indian investments. Understand the trade-offs. Leave with a dated action plan.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-ink/85">
          Aegis Plan India is a research desk and financial-planning simulator. It will not place a SIP,
          redeem a fund, or send money anywhere. Protect, Balance and Grow are three educational
          allocations — Grow is more aggressive, not better.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/onboarding"
            className="bg-navy px-5 py-3 text-sm text-paper hover:bg-navy-deep"
          >
            Start a household profile
          </Link>
          <Link href="/onboarding?demo=2" className="border border-navy px-5 py-3 text-sm text-navy">
            Load demo household #2
          </Link>
        </div>
        <section className="mt-12 border-t border-rule pt-8">
          <h2 className="font-display text-2xl text-navy">How a plan is made</h2>
          <ol className="mt-4 space-y-3 text-ink/90">
            <li>1. Household, goals, constraints and tax regime are captured.</li>
            <li>2. Holdings are parsed after deterministic PII redaction.</li>
            <li>3. A regulatory snapshot is frozen — tax and NPS rules are not invented by the model.</li>
            <li>4. Python builds three scenarios; a Risk Officer can veto. The LLM only explains.</li>
            <li>5. You compare, select, and download a dated Aegis Financial Action Plan.</li>
          </ol>
        </section>
      </article>
      <aside className="border border-rule bg-navy p-6 text-paper">
        <p className="font-display text-xl">Mandate</p>
        <p className="mt-4 text-sm leading-6 text-paper/90">{DISCLAIMER}</p>
        <p className="mt-6 text-sm text-brass">{NO_EXECUTION}</p>
        <dl className="mt-8 space-y-3 text-sm">
          <div className="flex justify-between border-b border-white/15 pb-2">
            <dt>Modes</dt>
            <dd>Educational / simulation</dd>
          </div>
          <div className="flex justify-between border-b border-white/15 pb-2">
            <dt>Default data</dt>
            <dd>Mock fixtures</dd>
          </div>
          <div className="flex justify-between pb-2">
            <dt>Execution</dt>
            <dd>None</dd>
          </div>
        </dl>
      </aside>
    </div>
  );
}
