"use client";

import { useState } from "react";

import type { BlogIdeaSummary } from "./page";
import { BatchActionBar } from "@/components/admin/batch-action-bar";
import { BlogIdeaCardList } from "./idea-card-list";

type Props = {
  ideas: BlogIdeaSummary[];
  approveIdeaAction: (formData: FormData) => Promise<void>;
  rejectIdeaAction: (formData: FormData) => Promise<void>;
};

export function BlogIdeaPageClient({
  ideas,
  approveIdeaAction,
  rejectIdeaAction,
}: Props) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleId = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <>
      <BatchActionBar
        selectedIds={Array.from(selectedIds)}
        onClear={() => setSelectedIds(new Set())}
      />
      <BlogIdeaCardList
        ideas={ideas}
        approveIdeaAction={approveIdeaAction}
        rejectIdeaAction={rejectIdeaAction}
        selectedIds={selectedIds}
        onToggleSelect={toggleId}
      />
    </>
  );
}
