import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      className={cn(
        "flex h-12 w-full rounded-2xl border-0 bg-[#1d1d1f]/[0.04] px-5 py-2 text-[15px] text-[#1d1d1f] placeholder:text-[#6e6e73]/60 transition-all duration-300 focus-visible:outline-none focus-visible:bg-[#1d1d1f]/[0.06] focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-40",
        className
      )}
      ref={ref}
      {...props}
    />
  )
);
Input.displayName = "Input";

export { Input };