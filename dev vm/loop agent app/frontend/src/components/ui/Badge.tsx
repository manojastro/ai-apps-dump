import { cn, statusTone } from "@/lib/utils";

export default function Badge({ children, status }: { children: React.ReactNode; status?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded border text-[11px] font-medium tracking-wide",
        statusTone(status || String(children))
      )}
    >
      {children}
    </span>
  );
}
