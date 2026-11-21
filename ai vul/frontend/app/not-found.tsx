import Link from "next/link";

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center px-4 text-center">
      <div>
        <div className="text-4xl font-semibold">404</div>
        <p className="mt-2 text-sm text-muted-foreground">This page does not exist.</p>
        <Link href="/dashboard" className="mt-4 inline-block text-sm text-primary hover:underline">Back to dashboard</Link>
      </div>
    </div>
  );
}
