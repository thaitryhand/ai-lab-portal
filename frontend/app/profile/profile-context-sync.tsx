"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useSession } from "@/components/session-provider";

export function ProfileContextSync() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshProfile } = useSession();
  const profileUpdated = searchParams.get("profileUpdated");

  useEffect(() => {
    if (!profileUpdated) return;
    refreshProfile().finally(() => {
      router.replace("/profile", { scroll: false });
    });
  }, [profileUpdated, refreshProfile, router]);

  return null;
}
