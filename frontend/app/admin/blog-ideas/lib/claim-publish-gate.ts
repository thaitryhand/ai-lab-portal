export type ClaimStatus = "pending" | "supported" | "unsupported" | "waived";

export type ClaimSummary = {
  total: number;
  pending: number;
  supported: number;
  waived: number;
  unsupported: number;
  blocking: number;
};

export type ClaimLike = {
  status: ClaimStatus;
};

export function summarizeClaims(claims: ClaimLike[]): ClaimSummary {
  const summary: ClaimSummary = {
    total: claims.length,
    pending: 0,
    supported: 0,
    waived: 0,
    unsupported: 0,
    blocking: 0,
  };
  for (const claim of claims) {
    summary[claim.status] += 1;
    if (claim.status === "pending" || claim.status === "unsupported") {
      summary.blocking += 1;
    }
  }
  return summary;
}

export function claimsBlockPublish(claims: ClaimLike[]): boolean {
  return summarizeClaims(claims).blocking > 0;
}
