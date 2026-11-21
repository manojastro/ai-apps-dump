import Link from "next/link";

export default function NotFound() {
  return (
    <div className="card mx-auto mt-16 max-w-lg p-6">
      <h1 className="text-lg font-semibold">Not found</h1>
      <p className="mt-2 text-[13px] text-slate-400">That route is not part of AI Career OS.</p>
      <Link href="/dashboard" className="mt-3 inline-block text-cyan-300">
        Back to command center
      </Link>
    </div>
  );
}
