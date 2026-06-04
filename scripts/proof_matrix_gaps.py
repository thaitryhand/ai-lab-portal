#!/usr/bin/env python3
"""Report actionable Harness proof gaps.

The installed Harness CLI stores proof flags as numeric booleans. This companion
script adds a read-only reporting convention for not-applicable proof layers:
put markers such as `platform:n/a` or `unit:n/a` in a story's evidence or notes.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

LAYERS: tuple[tuple[str, str], ...] = (
    ("unit", "unit_proof"),
    ("integration", "integration_proof"),
    ("e2e", "e2e_proof"),
    ("platform", "platform_proof"),
)


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "AGENTS.md").exists() and (candidate / "scripts").is_dir():
            return candidate
    return start


def has_na_marker(row: sqlite3.Row, layer: str) -> bool:
    haystack = f"{row['evidence'] or ''}\n{row['notes'] or ''}".lower()
    return f"{layer}:n/a" in haystack or f"{layer}:na" in haystack


def table(rows: list[list[str]]) -> str:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines: list[str] = []
    for index, row in enumerate(rows):
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
        if index == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report Harness proof gaps with n/a markers")
    parser.add_argument("--db", default=None, help="Path to harness.db (defaults to repo root/harness.db)")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    db_path = Path(args.db) if args.db else repo_root / "harness.db"
    if not db_path.exists():
        raise SystemExit(f"Harness database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        stories = conn.execute(
            """
            SELECT id, title, unit_proof, integration_proof, e2e_proof,
                   platform_proof, evidence, notes
            FROM story
            ORDER BY id
            """
        ).fetchall()

    summary: dict[str, dict[str, int]] = {
        layer: {"yes": 0, "missing": 0, "n/a": 0} for layer, _ in LAYERS
    }
    missing_rows: list[list[str]] = [["story", "title", "missing proof"]]

    for story in stories:
        missing_layers: list[str] = []
        for layer, column in LAYERS:
            if story[column]:
                summary[layer]["yes"] += 1
            elif has_na_marker(story, layer):
                summary[layer]["n/a"] += 1
            else:
                summary[layer]["missing"] += 1
                missing_layers.append(layer)
        if missing_layers:
            missing_rows.append([
                story["id"],
                story["title"][:64],
                ", ".join(missing_layers),
            ])

    print(f"Proof matrix gap audit: {len(stories)} stor{'y' if len(stories) == 1 else 'ies'}")
    print(table([["layer", "yes", "missing", "n/a"], *[
        [layer, str(counts["yes"]), str(counts["missing"]), str(counts["n/a"])]
        for layer, counts in summary.items()
    ]]))

    if len(missing_rows) > 1:
        print("\nActionable missing proof:")
        print(table(missing_rows))
    else:
        print("\nNo actionable missing proof found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
