"use client";

import { useRef, useState } from "react";
import { Camera, ImageIcon, Loader2, Upload, X } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { uploadImage } from "@/lib/upload";
import { cn } from "@/lib/utils";

type ImageUploadFieldProps = {
  /** Field name for the hidden URL input (submitted with the form). */
  name: string;
  /** Initial URL of the existing image. */
  initialUrl?: string;
  /** Aspect ratio class for the compact preview and dialog crop preview. */
  aspectClass?: string;
  /** Rounded class for the preview area. */
  roundedClass?: string;
  /** Label shown above the field. */
  label: string;
  /** Short description shown in the compact card. */
  description?: string;
  /** Placeholder shown in the URL fallback. */
  placeholder?: string;
  /** Hint text shown inside the dialog. */
  hint?: string;
  /** Smaller avatar-like presentation. */
  variant?: "avatar" | "cover";
};

export function ImageUploadField({
  name,
  initialUrl,
  aspectClass = "aspect-square",
  roundedClass = "rounded-2xl",
  label,
  description,
  placeholder = "https://example.com/image.png",
  hint,
  variant = "cover",
}: ImageUploadFieldProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [open, setOpen] = useState(false);
  const [imageUrl, setImageUrl] = useState(initialUrl ?? "");
  const [draftUrl, setDraftUrl] = useState(initialUrl ?? "");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File too large. Max 10MB.");
      return;
    }

    setError(null);
    setUploading(true);
    try {
      const url = await uploadImage(file);
      setDraftUrl(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();

  const saveDraft = () => {
    setImageUrl(draftUrl.trim());
    setError(null);
    setOpen(false);
  };

  const clearImage = () => {
    setImageUrl("");
    setDraftUrl("");
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const compactPreview = imageUrl;
  const previewSize = variant === "avatar" ? "size-20 sm:size-24" : "w-40 sm:w-52";

  return (
    <div className="rounded-2xl border border-border/70 bg-background/60 p-4 shadow-sm transition-colors hover:border-border">
      <input type="hidden" name={name} value={imageUrl} />

      <div className="flex items-center gap-4">
        <div
          className={cn(
            "relative shrink-0 overflow-hidden border border-border/70 bg-muted/40",
            previewSize,
            variant === "avatar" ? "rounded-full aspect-square" : cn("rounded-xl", aspectClass),
          )}
        >
          {compactPreview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={compactPreview} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand/10 via-muted/30 to-brand/20">
              {variant === "avatar" ? (
                <Camera className="size-5 text-muted-foreground/50" />
              ) : (
                <ImageIcon className="size-5 text-muted-foreground/50" />
              )}
            </div>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-foreground">{label}</p>
            {imageUrl ? (
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                Set
              </span>
            ) : null}
          </div>
          {description && (
            <p className="mt-1 max-w-md text-xs leading-5 text-muted-foreground">
              {description}
            </p>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Dialog open={open} onOpenChange={(next) => {
              setOpen(next);
              if (next) {
                setDraftUrl(imageUrl);
                setError(null);
              }
            }}>
              <DialogTrigger asChild>
                <button
                  type="button"
                  className="inline-flex h-9 items-center gap-2 rounded-full border border-border/80 bg-card px-3.5 text-xs font-medium text-foreground shadow-sm transition-colors hover:bg-muted"
                >
                  <Upload className="size-3.5" />
                  {imageUrl ? "Change" : "Upload"}
                </button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-xl">
                <DialogHeader>
                  <DialogTitle>{label}</DialogTitle>
                  <DialogDescription>
                    {hint ?? "Upload an image or paste an image URL."}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                  <button
                    type="button"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onClick={() => fileInputRef.current?.click()}
                    className={cn(
                      "relative w-full cursor-pointer overflow-hidden border-2 border-dashed border-border/60 bg-muted/30 transition-colors hover:border-brand/40 hover:bg-muted/50",
                      aspectClass,
                      roundedClass,
                      draftUrl && "border-solid border-border/80",
                    )}
                  >
                    {draftUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={draftUrl} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 p-6 text-center">
                        <ImageIcon className="size-7 text-muted-foreground/40" />
                        <span className="text-sm font-medium text-foreground">Click or drag to upload</span>
                        <span className="text-xs text-muted-foreground">JPG, PNG, WebP, GIF, AVIF · max 10MB</span>
                      </div>
                    )}

                    {uploading && (
                      <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/65 backdrop-blur-sm">
                        <Loader2 className="size-6 animate-spin text-muted-foreground" />
                      </div>
                    )}

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp,image/gif,image/avif"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFile(file);
                      }}
                    />
                  </button>

                  <div className="space-y-1.5">
                    <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Or paste an image URL
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        inputMode="url"
                        autoComplete="off"
                        value={draftUrl}
                        placeholder={placeholder}
                        className="h-11 w-full rounded-xl border border-border/80 bg-background px-4 pr-10 text-sm text-foreground placeholder:text-muted-foreground/50 transition-colors focus:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/10"
                        onChange={(e) => {
                          setDraftUrl(e.target.value);
                          setError(null);
                        }}
                      />
                      {draftUrl && (
                        <button
                          type="button"
                          onClick={() => setDraftUrl("")}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-muted-foreground"
                        >
                          <X className="size-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {error && (
                    <p className="flex items-center gap-1.5 text-xs font-medium text-destructive">
                      <Upload className="size-3" />
                      {error}
                    </p>
                  )}

                  <div className="flex items-center justify-between border-t border-border/50 pt-4">
                    <button
                      type="button"
                      onClick={clearImage}
                      className="text-sm font-medium text-muted-foreground underline underline-offset-4 hover:text-foreground"
                    >
                      Remove image
                    </button>
                    <button
                      type="button"
                      onClick={saveDraft}
                      disabled={uploading}
                      className="inline-flex h-10 items-center rounded-full bg-foreground px-5 text-sm font-medium text-background shadow-sm transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Use image
                    </button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            {imageUrl && (
              <button
                type="button"
                onClick={clearImage}
                className="text-xs font-medium text-muted-foreground underline underline-offset-4 hover:text-foreground"
              >
                Remove
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
