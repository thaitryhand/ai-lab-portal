"""Readability analysis for blog drafts using Flesch Reading Ease.

Pure Python implementation — no LLM call needed.
Provides deterministic readability metrics and suggestions.
"""

from __future__ import annotations

import re
from statistics import mean

from backend.app.llm.schemas import ReadabilityScore


# ── Syllable counting (approximate) ──────────────────────────────

_VOWELS = set("aeiouy")


def _count_syllables(word: str) -> int:
    """Approximate syllable count for a word."""
    word = word.lower().strip(".,!?;:\"'()[]{}")
    if not word:
        return 0

    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in _VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    if count == 0:
        count = 1
    # Adjust for silent 'e' at end
    if word.endswith("e") and count > 1:
        count -= 1
    # Ensure at least 1 syllable per word
    return max(1, count)


# ── Main analyzer ────────────────────────────────────────────────


def analyze_readability(text: str) -> ReadabilityScore:
    """Analyze readability of a text and return metrics.

    Uses Flesch Reading Ease formula:
        206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)

    Args:
        text: The text content to analyze.

    Returns:
        A ReadabilityScore with metrics and suggestions.
    """
    if not text.strip():
        return ReadabilityScore(
            flesch_reading_ease=50.0,
            avg_sentence_length=0,
            avg_word_length=0,
            reading_level="middle_school",
            suggestions=["No content to analyze"],
        )

    # Split into sentences
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences) or 1

    # Split into words
    words = re.findall(r"[a-zA-Z]+", text)
    word_count = len(words) or 1

    # Calculate metrics
    avg_sentence_length = word_count / sentence_count

    word_lengths = [len(w) for w in words]
    avg_word_length = mean(word_lengths) if word_lengths else 0

    total_syllables = sum(_count_syllables(w) for w in words)

    # Flesch Reading Ease
    flesch = (
        206.835
        - 1.015 * avg_sentence_length
        - 84.6 * (total_syllables / word_count)
    )
    flesch = max(0.0, min(100.0, flesch))

    # Reading level
    if flesch >= 80:
        reading_level = "elementary"
    elif flesch >= 60:
        reading_level = "middle_school"
    elif flesch >= 40:
        reading_level = "high_school"
    else:
        reading_level = "college"

    # Suggestions
    suggestions = []
    if avg_sentence_length > 25:
        suggestions.append(
            f"Sentences are long ({avg_sentence_length:.0f} words avg). "
            "Consider breaking into shorter sentences."
        )
    if avg_word_length > 6:
        suggestions.append(
            f"Words are complex ({avg_word_length:.1f} chars avg). "
            "Consider using simpler vocabulary."
        )
    if flesch < 40:
        suggestions.append(
            "Text is difficult to read (college level+). "
            "Aim for shorter sentences and simpler words."
        )
    if flesch > 90 and word_count > 100:
        suggestions.append(
            "Text is very easy to read — consider adding more depth "
            "for a technical audience."
        )

    return ReadabilityScore(
        flesch_reading_ease=round(flesch, 1),
        avg_sentence_length=round(avg_sentence_length, 1),
        avg_word_length=round(avg_word_length, 1),
        reading_level=reading_level,
        suggestions=suggestions,
    )


def reading_level_label(level: str) -> str:
    """Return a human-readable label for a reading level."""
    labels = {
        "elementary": "Elementary",
        "middle_school": "Middle School",
        "high_school": "High School",
        "college": "College / Advanced",
    }
    return labels.get(level, level)


def flesch_label(score: float) -> str:
    """Return a difficulty label for a Flesch score."""
    if score >= 80:
        return "Very easy"
    if score >= 60:
        return "Easy"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Difficult"
    return "Very difficult"
