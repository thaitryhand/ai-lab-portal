"""URL canonicalization and exact deduplication for extracted articles (US-039)."""

from __future__ import annotations

from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import BaseModel

from backend.app.news_extraction import ExtractedArticle, ExtractedArticleRepository

DuplicateStatus = Literal["unique", "url_duplicate", "content_duplicate"]

_TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "mc_")


class DedupResult(BaseModel):
    extraction_id: str
    canonical_url_normalized: str
    duplicate_status: DuplicateStatus
    duplicate_of_id: str | None = None


def canonicalize_url(url: str) -> str:
    """Normalize URL for exact-match deduplication."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must use http or https")

    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("URL must include a hostname")

    port = parsed.port
    if port is None:
        netloc = host
    elif (parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443):
        netloc = host
    else:
        netloc = f"{host}:{port}"

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    filtered_params: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered == "fbclid" or lowered == "gclid":
            continue
        if any(lowered.startswith(prefix) for prefix in _TRACKING_QUERY_PREFIXES):
            continue
        filtered_params.append((key, value))
    filtered_params.sort()
    query = urlencode(filtered_params)

    return urlunparse((parsed.scheme.lower(), netloc, path, "", query, ""))


def _article_url(article: ExtractedArticle) -> str:
    return article.canonical_url or article.final_url or article.source_url


def apply_dedup(
    extraction_id: str,
    *,
    extracted: ExtractedArticleRepository,
) -> DedupResult:
    article = extracted.get_by_id(extraction_id)
    if article is None:
        raise ValueError(f"Extraction not found: {extraction_id}")

    if article.extraction_status != "success":
        normalized = canonicalize_url(_article_url(article)) if _article_url(article) else ""
        updated = extracted.update_dedup_fields(
            extraction_id,
            canonical_url_normalized=normalized,
            duplicate_status="unique",
            duplicate_of_id=None,
        )
        if updated is None:
            raise ValueError(f"Extraction not found: {extraction_id}")
        return DedupResult(
            extraction_id=updated.id,
            canonical_url_normalized=updated.canonical_url_normalized,
            duplicate_status=updated.duplicate_status,
            duplicate_of_id=updated.duplicate_of_id,
        )

    normalized = canonicalize_url(_article_url(article))
    url_owner = extracted.find_earliest_by_canonical_url(normalized, exclude_id=extraction_id)
    if url_owner is not None:
        updated = extracted.update_dedup_fields(
            extraction_id,
            canonical_url_normalized=normalized,
            duplicate_status="url_duplicate",
            duplicate_of_id=url_owner,
        )
        if updated is None:
            raise ValueError(f"Extraction not found: {extraction_id}")
        return DedupResult(
            extraction_id=updated.id,
            canonical_url_normalized=updated.canonical_url_normalized,
            duplicate_status=updated.duplicate_status,
            duplicate_of_id=updated.duplicate_of_id,
        )

    hash_owner = extracted.find_earliest_by_content_hash(
        article.content_hash, exclude_id=extraction_id
    )
    if hash_owner is not None:
        updated = extracted.update_dedup_fields(
            extraction_id,
            canonical_url_normalized=normalized,
            duplicate_status="content_duplicate",
            duplicate_of_id=hash_owner,
        )
        if updated is None:
            raise ValueError(f"Extraction not found: {extraction_id}")
        return DedupResult(
            extraction_id=updated.id,
            canonical_url_normalized=updated.canonical_url_normalized,
            duplicate_status=updated.duplicate_status,
            duplicate_of_id=updated.duplicate_of_id,
        )

    updated = extracted.update_dedup_fields(
        extraction_id,
        canonical_url_normalized=normalized,
        duplicate_status="unique",
        duplicate_of_id=None,
    )
    if updated is None:
        raise ValueError(f"Extraction not found: {extraction_id}")
    return DedupResult(
        extraction_id=updated.id,
        canonical_url_normalized=updated.canonical_url_normalized,
        duplicate_status=updated.duplicate_status,
        duplicate_of_id=updated.duplicate_of_id,
    )
