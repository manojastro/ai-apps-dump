import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-[#1d1d1f]/[0.05]">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-3 px-6 py-8 sm:flex-row">
        <p className="text-[12px] text-[#6e6e73]">
          ResumeAI · Drafts stay in this browser
        </p>
        <div className="flex items-center gap-6">
          <Link
            href="/resume-builder"
            className="text-[12px] text-[#6e6e73] transition-colors hover:text-[#1d1d1f]"
          >
            Resume
          </Link>
          <Link
            href="/job-trends"
            className="text-[12px] text-[#6e6e73] transition-colors hover:text-[#1d1d1f]"
          >
            Jobs
          </Link>
        </div>
      </div>
    </footer>
  );
}
