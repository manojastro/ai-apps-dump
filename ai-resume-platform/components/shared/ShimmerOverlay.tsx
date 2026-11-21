"use client";

export function ShimmerOverlay() {
  return (
    <div className="absolute inset-0 z-10 overflow-hidden pointer-events-none">
      <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px]" />
      <div
        className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite]"
        style={{
          background:
            "linear-gradient(90deg, transparent 0%, rgba(0,113,227,0.06) 50%, transparent 100%)",
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex items-center gap-2 rounded-full bg-[#1d1d1f]/90 px-4 py-2">
          <div className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
          <p className="text-[12px] text-white font-medium">AI is enhancing...</p>
        </div>
      </div>
    </div>
  );
}