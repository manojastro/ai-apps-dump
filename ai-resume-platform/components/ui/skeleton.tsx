import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-2xl bg-[#1d1d1f]/[0.04]", className)}
      {...props}
    />
  );
}

export { Skeleton };