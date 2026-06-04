"use client";

import { useEffect, useState } from "react";
import { Camera } from "lucide-react";

import { cn } from "@/lib/utils";

export function AvatarUploadPreview({
  initialUrl,
  name,
}: {
  initialUrl?: string;
  name: string;
}) {
  const [previewUrl, setPreviewUrl] = useState(initialUrl ?? "");
  const [error, setError] = useState(false);

  useEffect(() => {
    const input = document.querySelector<HTMLInputElement>('input[name="avatarUrl"]');
    if (!input) return;

    const handler = () => {
      setPreviewUrl(input.value);
      setError(false);
    };
    input.addEventListener("input", handler);
    return () => input.removeEventListener("input", handler);
  }, []);

  const showFallback = !previewUrl || error;
  const initial = name?.charAt(0)?.toUpperCase() ?? "?";

  return (
    <div className="relative shrink-0">
      <div
        className={cn(
          "h-20 w-20 sm:h-24 sm:w-24 overflow-hidden rounded-full ring-4 ring-background bg-muted",
        )}
      >
        {showFallback ? (
          <span className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand/70 to-brand text-brand-foreground font-bold text-2xl sm:text-3xl select-none">
            {initial}
          </span>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={previewUrl}
            alt=""
            className="h-full w-full object-cover"
            onError={() => setError(true)}
            onLoad={() => setError(false)}
          />
        )}
      </div>
      <span className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full border-2 border-background bg-muted text-muted-foreground">
        <Camera className="size-3" />
      </span>
    </div>
  );
}
