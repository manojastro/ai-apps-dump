import { DISCLAIMER } from "@/lib/disclaimer";

export function DisclaimerBar() {
  return (
    <footer className="mt-12 border-t border-rule bg-raised px-5 py-4 text-xs leading-5 text-ink/80">
      <div className="mx-auto max-w-6xl">{DISCLAIMER}</div>
    </footer>
  );
}
