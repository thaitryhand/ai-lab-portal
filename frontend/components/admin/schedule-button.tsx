"use client";

import { useCallback, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

type Props = {
  ideaId: string;
  scheduledAt: string | null | undefined;
};

export function ScheduleButton({ ideaId, scheduledAt }: Props) {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  const schedule = useCallback(
    async (dateStr: string) => {
      setSaving(true);
      try {
        await fetch(`/api/admin/blog-ideas/${ideaId}/schedule`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scheduled_at: dateStr ? new Date(dateStr).toISOString() : null,
          }),
        });
        router.refresh();
      } finally {
        setSaving(false);
        setShowPicker(false);
      }
    },
    [ideaId, router],
  );

  return (
    <div className="flex items-center gap-2">
      {showPicker ? (
        <>
          <input
            type="datetime-local"
            className="rounded-md border border-border/60 bg-background px-2 py-1.5 text-xs"
            defaultValue={
              scheduledAt
                ? new Date(scheduledAt).toISOString().slice(0, 16)
                : ""
            }
            min={new Date().toISOString().slice(0, 16)}
            onChange={(e) => schedule(e.target.value)}
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowPicker(false)}
          >
            Cancel
          </Button>
        </>
      ) : (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowPicker(true)}
          disabled={saving}
        >
          {saving ? (
            <Loader2 className="size-3 animate-spin mr-1" />
          ) : (
            <CalendarDays className="size-3 mr-1" />
          )}
          {scheduledAt ? "Reschedule" : "Schedule"}
        </Button>
      )}
    </div>
  );
}
