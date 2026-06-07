"use client";

import { useCallback, useState } from "react";
import { ImageIcon, Loader2 } from "lucide-react";
import Image from "next/image";

import { Button } from "@/components/ui/button";

type Props = {
  ideaId: string;
  title: string;
};

export function ThumbnailButton({ ideaId, title }: Props) {
  const [loading, setLoading] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async () => {
    setLoading(true);
    setError(null);
    setImageUrl(null);

    try {
      const response = await fetch(
        `/api/admin/blog-ideas/${ideaId}/generate-thumbnail`,
        { method: "POST" },
      );
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        setError(text || `HTTP ${response.status}`);
        return;
      }
      const data = await response.json();
      setImageUrl(data.image_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setLoading(false);
    }
  }, [ideaId]);

  return (
    <div>
      <Button
        variant="outline"
        size="sm"
        onClick={generate}
        disabled={loading}
      >
        {loading ? (
          <Loader2 className="size-3 animate-spin mr-1" />
        ) : (
          <ImageIcon className="size-3 mr-1" />
        )}
        {imageUrl ? "Regenerate" : "AI Thumbnail"}
      </Button>
      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
      {imageUrl && (
        <div className="relative mt-2 aspect-video w-full max-w-sm overflow-hidden rounded-lg border border-border/60">
          <Image
            src={imageUrl}
            alt={`Thumbnail for ${title}`}
            fill
            className="object-cover"
            unoptimized
          />
        </div>
      )}
    </div>
  );
}
