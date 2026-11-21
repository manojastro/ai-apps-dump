import * as React from "react";
import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.ComponentProps<"textarea">
>(({ className, ...props }, ref) => (
  <textarea
    className={cn(
      "flex min-h-[140px] w-full rounded-2xl border-0 bg-[#1d1d1f]/[0.04] px-5 py-4 text-[15px] text-[#1d1d1f] placeholder:text-[#6e6e73]/60 transition-all duration-300 focus-visible:outline-none focus-visible:bg-[#1d1d1f]/[0.06] disabled:cursor-not-allowed disabled:opacity-40 resize-none leading-[1.6]",
      className
    )}
    ref={ref}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export { Textarea };