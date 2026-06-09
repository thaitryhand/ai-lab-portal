"use client";

import { useState } from "react";
import { Briefcase, Check, Copy, MessageCircle } from "lucide-react";

type Tweet = { number: number; content: string };
type TwitterThread = { tweets: Tweet[] } | null;
type LinkedInArticle = { headline: string; summary: string; key_takeaways: string[] } | null;

type RepurposedContent = {
  id: string;
  twitter_thread: TwitterThread;
  linkedin_article: LinkedInArticle;
  summary_snippet: string;
  created_at: string;
};

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      type="button"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted/50 hover:text-foreground"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied!" : label}
    </button>
  );
}

function formatTwitterThread(thread: TwitterThread): string {
  if (!thread) return "";
  return thread.tweets
    .map((t) => `${t.number}/${thread.tweets.length} ${t.content}`)
    .join("\n\n");
}

function formatLinkedInArticle(article: LinkedInArticle): string {
  if (!article) return "";
  const takeaways = article.key_takeaways
    .map((t, i) => `${i + 1}. ${t}`)
    .join("\n");
  return `${article.headline}\n\n${article.summary}\n\nKey Takeaways:\n${takeaways}`;
}

export function RepurposeClient({ content }: { content: RepurposedContent }) {
  return (
    <div className="space-y-6">
      {/* Summary snippet */}
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <MessageCircle className="h-4 w-4 text-sky-500" />
            Summary Snippet
          </h3>
          <CopyButton text={content.summary_snippet} label="Copy snippet" />
        </div>
        <p className="text-sm text-muted-foreground">{content.summary_snippet}</p>
      </div>

      {/* Twitter thread */}
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <MessageCircle className="h-4 w-4 text-sky-500" />
            Twitter Thread
          </h3>
          {content.twitter_thread && (
            <CopyButton text={formatTwitterThread(content.twitter_thread)} label="Copy all tweets" />
          )}
        </div>
        {content.twitter_thread ? (
          <div className="space-y-3">
            {content.twitter_thread.tweets.map((tweet) => (
              <div
                key={tweet.number}
                className="rounded-lg border border-border/60 bg-muted/20 p-4"
              >
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">
                    Tweet {tweet.number}/{content.twitter_thread!.tweets.length}
                  </span>
                  <CopyButton text={tweet.content} label="Copy" />
                </div>
                <p className="text-sm">{tweet.content}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No Twitter thread generated.</p>
        )}
      </div>

      {/* LinkedIn article */}
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <Briefcase className="h-4 w-4 text-blue-600" />
            LinkedIn Article
          </h3>
          {content.linkedin_article && (
            <CopyButton text={formatLinkedInArticle(content.linkedin_article)} label="Copy article" />
          )}
        </div>
        {content.linkedin_article ? (
          <div className="space-y-4">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Headline</p>
              <p className="text-sm font-semibold">{content.linkedin_article.headline}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Summary</p>
              <p className="text-sm text-muted-foreground">{content.linkedin_article.summary}</p>
            </div>
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">Key Takeaways</p>
              <ul className="space-y-1.5">
                {content.linkedin_article.key_takeaways.map((takeaway, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand/60" />
                    {takeaway}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No LinkedIn article generated.</p>
        )}
      </div>
    </div>
  );
}
