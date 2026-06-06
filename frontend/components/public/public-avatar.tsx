"use client";

import { cn } from "@/lib/utils";

type AvatarProps = {
  src?: string | null;
  name?: string | null;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
};

const sizeMap = {
  xs: "h-6 w-6 text-[9px]",
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-14 w-14 text-lg",
  xl: "h-20 w-20 text-2xl",
};

export function Avatar({ src, name, size = "sm", className }: AvatarProps) {
  const initial = (name ?? "?")[0]?.toUpperCase() ?? "?";

  if (src) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt=""
        className={cn(
          "rounded-full object-cover ring-1 ring-border",
          sizeMap[size],
          className,
        )}
      />
    );
  }

  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-gradient-to-br from-brand/70 to-brand text-brand-foreground font-semibold ring-1 ring-border select-none",
        sizeMap[size],
        className,
      )}
    >
      {initial}
    </div>
  );
}
