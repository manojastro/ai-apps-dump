import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-[13px] font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0071e3]/20 disabled:pointer-events-none disabled:opacity-30 cursor-pointer",
  {
    variants: {
      variant: {
        default:
          "bg-[#0071e3] text-white hover:bg-[#0077ed] hover:scale-[1.015] hover:shadow-md hover:shadow-[#0071e3]/20 active:scale-[0.98] rounded-full",
        destructive:
          "bg-[#ff3b30] text-white hover:bg-[#ff453a] hover:scale-[1.015] active:scale-[0.98] rounded-full",
        outline:
          "text-[#0071e3] hover:underline underline-offset-4 p-0 h-auto rounded-none",
        secondary:
          "bg-[#1d1d1f]/[0.06] text-[#1d1d1f] hover:bg-[#1d1d1f]/[0.1] active:scale-[0.98] rounded-full",
        ghost:
          "text-[#0071e3] hover:opacity-60 p-0 h-auto rounded-none",
        link:
          "text-[#0071e3] hover:opacity-60 p-0 h-auto rounded-none",
      },
      size: {
        default: "h-9 px-5",
        sm: "h-8 px-4 text-[12px]",
        lg: "h-11 px-7 text-[14px]",
        icon: "h-9 w-9 rounded-full hover:bg-[#1d1d1f]/[0.05]",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };