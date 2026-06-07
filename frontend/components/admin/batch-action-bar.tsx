"use client";

import { useCallback, useState } from "react";
import { CheckCircle, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Props = {
  selectedIds: string[];
  onClear: () => void;
};

export function BatchActionBar({ selectedIds, onClear }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const approveAll = useCallback(async () => {
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch("/api/admin/blog-ideas/batch/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: selectedIds }),
      });
      if (!response.ok) {
        setResult(`Error: HTTP ${response.status}`);
        return;
      }
      const data = await response.json();
      const ok = data.filter((r: { status: string }) => r.status === "approved").length;
      setResult(`Approved ${ok}/${selectedIds.length} ideas`);
      onClear();
      setTimeout(() => router.refresh(), 500);
    } catch (err) {
      setResult(err instanceof Error ? err.message : "Failed");
    } finally {
      setLoading(false);
    }
  }, [selectedIds, onClear, router]);

  if (selectedIds.length === 0) return null;

  return (
    <div
      className={cn(
        "sticky top-0 z-10 -mx-4 mb-4 rounded-xl border border-brand/30",
        "bg-brand/5 px-4 py-3 backdrop-blur-sm",
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium">
          {selectedIds.length} selected
        </p>
        <div className="flex items-center gap-2">
          {result && (
            <span className="text-xs text-emerald-600">{result}</span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={onClear}
            disabled={loading}
          >
            Clear
          </Button>
          <Button
            variant="brand"
            size="sm"
            onClick={approveAll}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="size-3 animate-spin mr-1" />
            ) : (
              <CheckCircle className="size-3 mr-1" />
            )}
            Approve all
          </Button>
        </div>
      </div>
    </div>
  );
}
