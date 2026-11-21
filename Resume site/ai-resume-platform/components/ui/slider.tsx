"use client";

import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

const Slider = React.forwardRef<
  React.ComponentRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn(
      "relative flex w-full touch-none select-none items-center py-3",
      className
    )}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-[3px] w-full grow overflow-hidden rounded-full bg-[#1d1d1f]/[0.08]">
      <SliderPrimitive.Range className="absolute h-full bg-[#1d1d1f]" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-5 w-5 rounded-full bg-white shadow-[0_1px_4px_rgba(0,0,0,0.15)] border border-[#1d1d1f]/[0.06] transition-transform focus-visible:outline-none hover:scale-110" />
    <SliderPrimitive.Thumb className="block h-5 w-5 rounded-full bg-white shadow-[0_1px_4px_rgba(0,0,0,0.15)] border border-[#1d1d1f]/[0.06] transition-transform focus-visible:outline-none hover:scale-110" />
  </SliderPrimitive.Root>
));
Slider.displayName = SliderPrimitive.Root.displayName;

export { Slider };