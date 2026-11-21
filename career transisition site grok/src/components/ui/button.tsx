import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-lg text-[13px] font-medium tracking-[-0.01em] disabled:pointer-events-none disabled:opacity-50 min-h-9 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-cyan-400 text-slate-950 shadow-[0_0_0_1px_rgb(34_211_238_/_0.25),0_8px_20px_rgb(34_211_238_/_0.12)] hover:bg-cyan-300",
        emerald:
          "bg-emerald-400 text-slate-950 shadow-[0_0_0_1px_rgb(52_211_153_/_0.25)] hover:bg-emerald-300",
        ghost: "text-slate-300 hover:bg-white/6 hover:text-white",
        outline:
          "border border-white/12 bg-white/[0.02] text-slate-200 hover:border-white/20 hover:bg-white/6",
        danger: "bg-rose-500/15 text-rose-200 hover:bg-rose-500/25",
      },
      size: {
        sm: "h-8 px-2.5",
        md: "h-9 px-3",
        lg: "h-10 px-4",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: { variant: "default", size: "md" },
  },
);

export function Button({
  className,
  variant,
  size,
  asChild,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
