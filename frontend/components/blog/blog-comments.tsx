"use client";

import { useState, useOptimistic, startTransition } from "react";
import Link from "next/link";
import { SendHorizonal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { BlogCommentPublic } from "@/lib/blog/social";
import { cn } from "@/lib/utils";

type Props = {
  slug: string;
  initialComments: BlogCommentPublic[];
  isAuthenticated: boolean;
  onCreateComment?: (slug: string, content: string, parentId: string | undefined) => Promise<void>;
};

type CommentNode = BlogCommentPublic & { replies: CommentNode[] };

const MAX_THREAD_DEPTH = 3;

function formatDate(dateStr: string) {
  try {
    const ms = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(ms / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return dateStr;
  }
}

function buildTree(comments: BlogCommentPublic[]): CommentNode[] {
  const nodes = new Map<string, CommentNode>();
  const roots: CommentNode[] = [];

  for (const comment of comments) nodes.set(comment.id, { ...comment, replies: [] });

  for (const node of nodes.values()) {
    const parent = node.parent_id ? nodes.get(node.parent_id) : undefined;
    if (parent) parent.replies.push(node);
    else roots.push(node);
  }

  const byDate = (a: CommentNode, b: CommentNode) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
  function sort(nodesToSort: CommentNode[]) {
    nodesToSort.sort(byDate);
    for (const node of nodesToSort) sort(node.replies);
  }
  sort(roots);
  return roots;
}

function Avatar({ comment }: { comment: BlogCommentPublic }) {
  if (comment.avatar_url) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img alt="" className="size-7 rounded-full object-cover" src={comment.avatar_url} />;
  }
  return (
    <div className="flex size-7 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
      {(comment.user_name ?? "A")[0].toUpperCase()}
    </div>
  );
}

function CommentCard({
  node,
  depth,
  isAuthenticated,
  onReply,
}: {
  node: CommentNode;
  depth: number;
  isAuthenticated: boolean;
  onReply?: (parentId: string) => void;
}) {
  const canNest = depth < MAX_THREAD_DEPTH - 1;
  const nestedDepth = Math.min(depth, MAX_THREAD_DEPTH - 1);

  return (
    <div className={cn("space-y-3", nestedDepth > 0 && "border-l border-border pl-4")} id={`comment-${node.id}`}>
      <div className="space-y-1.5">
        <div className="flex items-center gap-2">
          <Link href={`/profiles/${node.user_id}`} className="shrink-0">
            <Avatar comment={node} />
          </Link>
          <Link href={`/profiles/${node.user_id}`} className="text-sm font-medium hover:text-brand">
            {node.user_name ?? "Anonymous"}
          </Link>
          <span className="text-xs text-muted-foreground">{formatDate(node.created_at)}</span>
        </div>
        <p className="ml-9 text-sm leading-relaxed text-foreground/85">{node.content}</p>
        {isAuthenticated && onReply && (
          <button
            type="button"
            onClick={() => onReply(node.id)}
            className="ml-9 text-xs text-muted-foreground hover:text-foreground"
          >
            Reply
          </button>
        )}
      </div>

      {node.replies.length > 0 && (
        <div className="ml-5 flex flex-col gap-4">
          {node.replies.map((reply) => (
            <CommentCard
              key={reply.id}
              node={reply}
              depth={canNest ? depth + 1 : depth}
              isAuthenticated={isAuthenticated}
              onReply={onReply}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function BlogComments({
  slug,
  initialComments,
  isAuthenticated,
  onCreateComment,
}: Props) {
  const [comments, setComments] = useOptimistic(initialComments);
  const [content, setContent] = useState("");
  const [replyTo, setReplyTo] = useState<string | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim() || !onCreateComment || isSubmitting) return;

    const trimmedContent = content.trim();
    const parentId = replyTo;

    setIsSubmitting(true);
    startTransition(async () => {
      const optimisticComment: BlogCommentPublic = {
        id: `optimistic-${Date.now()}`,
        user_id: "me",
        user_name: "You",
        avatar_url: null,
        content: trimmedContent,
        parent_id: parentId ?? null,
        created_at: new Date().toISOString(),
      };
      setComments((prev) => [...prev, optimisticComment]);
      try {
        await onCreateComment(slug, trimmedContent, parentId);
        setContent("");
        setReplyTo(undefined);
      } finally {
        setIsSubmitting(false);
      }
    });
  }

  const tree = buildTree(comments);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Comments ({comments.length})</h3>

      {!isAuthenticated ? (
        <p className="text-sm text-muted-foreground">
          <Link href="/login" className="font-medium text-brand underline underline-offset-2 hover:text-brand/80">
            Sign in
          </Link>{" "}
          to leave a comment.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          {replyTo && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>Replying in thread</span>
              <button type="button" onClick={() => setReplyTo(undefined)} className="font-medium text-brand hover:text-brand/80">
                Cancel
              </button>
            </div>
          )}
          <div className="relative">
            <Input
              placeholder={replyTo ? "Write a reply..." : "Share your thoughts..."}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={isSubmitting}
              className="pr-12"
              maxLength={5000}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!content.trim() || isSubmitting}
              className="absolute right-1 top-1/2 size-8 -translate-y-1/2"
              variant="ghost"
            >
              <SendHorizonal className="size-4" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">New comments appear after moderation approval.</p>
        </form>
      )}

      {tree.length === 0 ? (
        <p className="text-sm text-muted-foreground">No comments yet. Be the first to share your thoughts!</p>
      ) : (
        <div className="flex flex-col gap-5">
          {tree.map((node) => (
            <CommentCard
              key={node.id}
              node={node}
              depth={0}
              isAuthenticated={isAuthenticated}
              onReply={setReplyTo}
            />
          ))}
        </div>
      )}
    </div>
  );
}
