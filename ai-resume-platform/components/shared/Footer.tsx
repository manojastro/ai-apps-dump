import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-[#1d1d1f]/[0.04] mt-auto">
      <div className="mx-auto max-w-5xl px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-[11px] text-[#6e6e73]">
          Built for Indian job seekers
        </p>
        <div className="flex items-center gap-6">
          <Link href="/resume-builder" className="text-[11px] text-[#6e6e73] hover:text-[#1d1d1f] transition-colors">
            Resume
          </Link>
          <Link href="/job-trends" className="text-[11px] text-[#6e6e73] hover:text-[#1d1d1f] transition-colors">
            Jobs
          </Link>
        </div>
      </div>
    </footer>
  );
}