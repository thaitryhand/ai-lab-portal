#!/usr/bin/env python3
"""Backfill intake_id linkage for traces missing it.

Strategy (in order):
1. Direct story_id match: trace.story_id == intake.story_id
2. Fuzzy story_id match: trace story_id is contained in intake story_id list
3. Timestamp proximity: find nearest intake within +-2 hours
4. Report any remaining unlinked traces for manual review

Usage:
    python scripts/backfill_intake_linkage.py          # dry-run (default)
    python scripts/backfill_intake_linkage.py --apply   # apply changes
    python scripts/backfill_intake_linkage.py --report  # show unlinked traces
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Handle Windows console encoding
if sys.stdout.encoding is None or sys.stdout.encoding == "cp1252":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "AGENTS.md").exists() and (candidate / "scripts").is_dir():
            return candidate
    return start


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.fromisoformat(s)
        except (ValueError, TypeError):
            return None


def safe(s: str | None, maxlen: int = 100) -> str:
    """Return a safely printable string, replacing unencodable chars."""
    if s is None:
        return ""
    result = s[:maxlen]
    # Replace common problematic chars
    result = result.replace("\u2013", "-").replace("\u2014", "--")
    result = result.replace("\u2019", "'").replace("\u2018", "'")
    result = result.replace("\u201c", '"').replace("\u201d", '"')
    result = result.replace("\u2026", "...")
    # Strip any remaining non-ASCII that might cause issues
    return result.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill intake_id linkage for traces missing it."
    )
    parser.add_argument("--apply", action="store_true", help="Apply backfill (default: dry-run)")
    parser.add_argument("--report", action="store_true", help="Show unlinked traces after backfill")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    db_path = repo_root / "harness.db"
    if not db_path.exists():
        raise SystemExit(f"Harness database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Load all intakes
    intakes = conn.execute(
        "SELECT id, created_at, story_id, summary, input_type, risk_lane FROM intake ORDER BY created_at"
    ).fetchall()
    intake_by_story: dict[str, list[sqlite3.Row]] = defaultdict(list)
    intake_timeline: list[tuple[datetime, int, sqlite3.Row]] = []
    for intake in intakes:
        dt = parse_dt(intake["created_at"])
        if dt:
            intake_timeline.append((dt, intake["id"], intake))
        sid = (intake["story_id"] or "").strip()
        for s in sid.replace(",", " ").split():
            s = s.strip()
            if s:
                intake_by_story[s].append(intake)

    # Load traces missing intake_id
    traces = conn.execute(
        "SELECT id, created_at, story_id, task_summary FROM trace WHERE intake_id IS NULL ORDER BY created_at"
    ).fetchall()

    if not traces:
        print("No traces missing intake_id - linkage already complete.")
        conn.close()
        return 0

    total_traces = conn.execute("SELECT COUNT(*) FROM trace").fetchone()[0]
    print(f"== {len(traces)} traces missing intake_id (of {total_traces} total)")
    print(f"   {len(intakes)} intakes available")
    print()

    linked: list[tuple[int, int, str]] = []
    unlinked: list[sqlite3.Row] = []

    for trace in traces:
        trace_id = trace["id"]
        trace_story = (trace["story_id"] or "").strip()
        trace_dt = parse_dt(trace["created_at"])
        matched_intake_id = None
        method = ""

        # 1. Direct story_id match
        if trace_story and trace_story in intake_by_story:
            candidates = intake_by_story[trace_story]
            if len(candidates) == 1:
                matched_intake_id = candidates[0]["id"]
                method = f"story_id direct ({trace_story})"
            elif trace_dt:
                best = min(candidates, key=lambda c: abs((parse_dt(c["created_at"]) or datetime.min) - trace_dt))
                matched_intake_id = best["id"]
                method = f"story_id closest ({trace_story})"

        # 2. Timestamp proximity (within 2 hours)
        if matched_intake_id is None and trace_dt:
            best_diff = timedelta(hours=2)
            best_id = None
            for i_dt, i_id, i_row in intake_timeline:
                diff = abs(trace_dt - i_dt)
                if diff < best_diff:
                    best_diff = diff
                    best_id = i_id
            if best_id is not None:
                matched_intake_id = best_id
                mins = int(best_diff.total_seconds() / 60)
                method = f"timestamp proximity ({mins} min)"

        if matched_intake_id is not None:
            linked.append((trace_id, matched_intake_id, method))
        else:
            unlinked.append(trace)

    print(f"== Linked: {len(linked)}")
    print(f"== Unlinked: {len(unlinked)}")
    print()

    if linked:
        print("--- Linked traces ---")
        for trace_id, intake_id, method in linked:
            trace = next(t for t in traces if t["id"] == trace_id)
            intake = next(i for i in intakes if i["id"] == intake_id)
            print(f"  trace {trace_id} -> intake {intake_id} [{method}]")
            print(f"    trace: {safe(trace['task_summary'], 80)}")
            print(f"    intake: {safe(intake['summary'], 80)}")
            print()

    if unlinked:
        print("--- Unlinked traces (need manual review) ---")
        for t in unlinked:
            print(f"  trace {t['id']} ({t['created_at']}) story={t['story_id'] or 'none'}")
            print(f"    {safe(t['task_summary'], 100)}")
            print()

    if args.apply and linked:
        c = conn.cursor()
        for trace_id, intake_id, _ in linked:
            c.execute("UPDATE trace SET intake_id = ? WHERE id = ?", (intake_id, trace_id))
        conn.commit()
        print(f"Applied: {len(linked)} traces updated.")
    elif linked and not args.apply:
        print("(dry-run) Pass --apply to write changes.")
        print(f"   python scripts/backfill_intake_linkage.py --apply")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
