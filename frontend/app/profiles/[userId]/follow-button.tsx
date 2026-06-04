"use client";

import { useTransition } from "react";
import { UserPlus, UserCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { followProfileAction, unfollowProfileAction } from "./actions";

export function FollowButton({ userId, isFollowing }: { userId: string; isFollowing: boolean }) {
  const [isPending, startTransition] = useTransition();

  return (
    <Button
      type="button"
      variant={isFollowing ? "outline" : "default"}
      disabled={isPending}
      onClick={() => startTransition(() => (isFollowing ? unfollowProfileAction(userId) : followProfileAction(userId)))}
    >
      {isFollowing ? <UserCheck className="size-4" /> : <UserPlus className="size-4" />}
      {isFollowing ? "Following" : "Follow"}
    </Button>
  );
}
