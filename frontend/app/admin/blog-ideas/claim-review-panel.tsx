"use client";

import { useFormStatus } from "react-dom";
import { AlertTriangle, CheckCircle2, Search, ShieldOff, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";

import type { BlogClaimItem } from "./idea-detail-view";
import { summarizeClaims } from "./lib/claim-publish-gate";

const CLAIM_STATUS_STYLES: Record<BlogClaimItem["status"], string> = {
  pending:
    "text-amber-700 bg-amber-50 border-amber-200 dark:text-amber-300 dark:bg-amber-950/30 dark:border-amber-900",
  supported:
    "text-emerald-700 bg-emerald-50 border-emerald-200 dark:text-emerald-300 dark:bg-emerald-950/30 dark:border-emerald-900",
  waived:
    "text-sky-700 bg-sky-50 border-sky-200 dark:text-sky-300 dark:bg-sky-950/30 dark:border-sky-900",
  unsupported:
    "text-red-700 bg-red-50 border-red-200 dark:text-red-300 dark:bg-red-950/30 dark:border-red-900",
};

const EVIDENCE_SOURCES = [
  { value: "measurement", label: "Measurement / benchmark" },
  { value: "documentation", label: "Documentation" },
  { value: "expert", label: "Expert review" },
  { value: "customer", label: "Customer reference" },
  { value: "other", label: "Other" },
] as const;

const selectClassName =
  "flex h-9 w-full rounded-[var(--radius-admin-sm)] border border-input bg-background px-3 py-1.5 text-sm";

type ClaimActions = {
  extractClaims: (formData: FormData) => Promise<void>;
  updateClaim: (formData: FormData) => Promise<void>;
  waiveAllClaims: (formData: FormData) => Promise<void>;
};

type Props = {
  ideaId: string;
  claims: BlogClaimItem[];
  actions: ClaimActions;
};

function SubmitButton({
  label,
  variant = "default",
  icon: Icon,
}: {
  label: string;
  variant?: "default" | "outline" | "secondary";
  icon?: typeof CheckCircle2;
}) {
  const { pending } = useFormStatus();
  return (
    <Button disabled={pending} size="sm" type="submit" variant={variant}>
      {Icon ? <Icon className="size-3.5" aria-hidden /> : null}
      {pending ? "Saving…" : label}
    </Button>
  );
}

function ClaimStatusBadge({ status }: { status: BlogClaimItem["status"] }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-md border px-2 py-0.5 text-xs font-medium capitalize",
        CLAIM_STATUS_STYLES[status],
      )}
    >
      {status}
    </span>
  );
}

export function ClaimReviewPanel({ ideaId, claims, actions }: Props) {
  const summary = summarizeClaims(claims);
  const pendingClaims = claims.filter((c) => c.status === "pending");

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>{summary.total} total</span>
        <span>·</span>
        <span>{summary.pending} pending</span>
        <span>·</span>
        <span>{summary.supported} supported</span>
        <span>·</span>
        <span>{summary.waived} waived</span>
        {summary.unsupported > 0 ? (
          <>
            <span>·</span>
            <span>{summary.unsupported} unsupported</span>
          </>
        ) : null}
      </div>

      {summary.blocking > 0 ? (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/20 dark:text-amber-200">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>
            <strong>{summary.blocking}</strong> claim
            {summary.blocking === 1 ? "" : "s"} block publishing. Attach evidence,
            waive, or mark unsupported before publish.
          </p>
        </div>
      ) : claims.length > 0 ? (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50/70 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/20 dark:text-emerald-300">
          <CheckCircle2 className="size-4 shrink-0" aria-hidden />
          All claims cleared for publish.
        </div>
      ) : null}

      {claims.length === 0 ? (
        <>
          <form action={actions.extractClaims}>
            <input name="ideaId" type="hidden" value={ideaId} />
            <Button size="sm" type="submit" variant="secondary">
              <Search className="size-4" aria-hidden />
              Extract claims from draft
            </Button>
          </form>
          <p className="text-sm text-muted-foreground">
            No claims in the ledger yet. Extract claims before publishing quantified statements.
          </p>
        </>
      ) : (
        <>
          {pendingClaims.length > 1 ? (
            <form action={actions.waiveAllClaims}>
              <input name="ideaId" type="hidden" value={ideaId} />
              <SubmitButton label="Waive all pending" variant="outline" icon={ShieldOff} />
            </form>
          ) : null}

          <ul className="grid gap-3">
            {claims.map((claim) => (
              <li
                key={claim.id}
                className="rounded-lg border border-border bg-muted/30 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="text-sm font-medium text-foreground">{claim.claim_text}</p>
                  <ClaimStatusBadge status={claim.status} />
                </div>
                <p className="mt-1 text-xs text-muted-foreground capitalize">
                  {claim.claim_type.replace(/_/g, " ")}
                </p>

                {claim.evidence_source_type || claim.evidence_reference ? (
                  <div className="mt-3 rounded-md border border-border/60 bg-background/60 px-3 py-2 text-xs text-muted-foreground">
                    {claim.evidence_source_type ? (
                      <p>
                        <span className="font-medium text-foreground">Source:</span>{" "}
                        {claim.evidence_source_type}
                      </p>
                    ) : null}
                    {claim.evidence_reference ? (
                      <p className="mt-1 break-all">
                        <span className="font-medium text-foreground">Reference:</span>{" "}
                        {claim.evidence_reference}
                      </p>
                    ) : null}
                  </div>
                ) : null}

                {claim.status === "pending" ? (
                  <form action={actions.updateClaim} className="mt-3 grid gap-2">
                    <input name="claimId" type="hidden" value={claim.id} />
                    <input name="ideaId" type="hidden" value={ideaId} />
                    <label className="grid gap-1 text-xs font-medium text-foreground">
                      Evidence source
                      <select
                        className={selectClassName}
                        defaultValue=""
                        name="evidenceSource"
                        required
                      >
                        <option disabled value="">
                          Select source type
                        </option>
                        {EVIDENCE_SOURCES.map((source) => (
                          <option key={source.value} value={source.value}>
                            {source.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="grid gap-1 text-xs font-medium text-foreground">
                      Evidence reference
                      <input
                        className="rounded-md border border-border bg-background px-2 py-1.5 text-sm"
                        name="evidenceReference"
                        placeholder="Link, doc section, or measurement note"
                        required
                      />
                    </label>
                    <div className="flex flex-wrap gap-2 pt-1">
                      <SubmitButton label="Mark supported" icon={CheckCircle2} />
                      <button
                        className={cn(buttonVariants({ size: "sm", variant: "outline" }), "gap-1.5")}
                        name="waive"
                        type="submit"
                        value="on"
                      >
                        <ShieldOff className="size-3.5" aria-hidden />
                        Waive for publish
                      </button>
                      <button
                        className={cn(buttonVariants({ size: "sm", variant: "outline" }), "gap-1.5")}
                        name="unsupported"
                        type="submit"
                        value="on"
                      >
                        <XCircle className="size-3.5" aria-hidden />
                        Mark unsupported
                      </button>
                    </div>
                  </form>
                ) : null}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
