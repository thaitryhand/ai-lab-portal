# Agent Instructions

Add project-specific agent instructions here.

<!-- HARNESS:BEGIN -->
## Harness

This repo uses Harness. Before work, read:

- `README.md`
- `docs/HARNESS.md`
- `docs/FEATURE_INTAKE.md`
- `docs/ARCHITECTURE.md`
- `docs/CONTEXT_RULES.md`
- `scripts/bin/harness-cli query matrix` on macOS/Linux, or `.\scripts\bin\harness-cli.exe query matrix` on Windows

Use the Rust Harness CLI at `scripts/bin/harness-cli` on macOS/Linux or
`scripts/bin/harness-cli.exe` on Windows as the main operational tool.

After work, record a trace with `scripts/bin/harness-cli trace`. For
`harness_friction`, name only **new** pain. If the issue is already in
`scripts/bin/harness-cli query backlog`, reference that backlog id in `notes`
and use `harness_friction: none` unless something changed. See
`docs/TRACE_SPEC.md` (recurring friction deduplication).

### Trace Recording Checklist & Template

Before recording a trace:

1. **Ensure an intake was recorded** (if the work wasn't classified yet, run
   `scripts/bin/harness-cli intake --type <type> --summary "<text>" --lane <lane>` first).
   The trace's `--intake` field links back to the intake record, enabling
   feature-granular trace queries.

2. Fill all **Standard-tier** fields (required for normal-lane tasks;
   tiny-lane may use Minimal per TRACE_SPEC.md):

- [ ] `--summary` — one sentence naming outcome or attempted outcome
- [ ] `--outcome` — one of: `completed`, `blocked`, `partial`, `failed`
- [ ] `--agent` — short agent/tool name (e.g. `pi`, `codex`, `cursor`, `zed`)
- [ ] `--actions` — comma-separated list of concrete actions taken
- [ ] `--read` — comma-separated list of files/commands read
- [ ] `--changed` — comma-separated list of files changed (omit only if no files changed)
- [ ] `--friction` — name new pain, or `none` if actively checked; reference backlog id for recurring items
- [ ] `--intake` — intake id (when an intake was recorded)
- [ ] `--story` — story id (when work maps to one story)
- [ ] `--errors` — JSON array text, or `none` (required for Detailed traces)
- [ ] `--duration` — seconds estimate (required for Detailed)
- [ ] `--tokens` — token estimate (required for Detailed)
- [ ] `--decisions` — scope/validation choices (required for Detailed)

**Standard-tier template** (copy-paste, fill values):

```bash
scripts/bin/harness-cli trace \
  --summary "<one sentence naming outcome>" \
  --intake <id> \
  --story <ID> \
  --agent <name> \
  --outcome <completed|blocked|partial|failed> \
  --actions "<action1>,<action2>,<action3>" \
  --read "<file1>,<file2>,<command1>" \
  --changed "<file1>,<file2>" \
  --friction "<new pain or none>" \
  --duration <seconds_estimate> \
  --tokens <estimate>
```

**Important**: pass `--agent` and `--actions` explicitly — some agents
(cursor, zed, codex) may drop these flags across session continues if only
the summary is filled. Run `python scripts/trace_quality.py` after recording
to confirm zero core gaps.
<!-- HARNESS:END -->

## Tools RULES:
- Always use `srcwalk` skill: for best codebase/files/dirs exploration, discover, searching.
- Always prefer `srcwalk` CLI over read/glob/grep tool.
- Prefer `fd` over `find`.
- Prefer `rg` over `grep`.