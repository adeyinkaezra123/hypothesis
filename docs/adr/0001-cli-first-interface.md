# ADR 0001: CLI-first interface; TUI frozen until classification overrides

- Status: Accepted
- Date: 2026-07-06

## Context

hypothesis is a developer-first CLI for realistic, foreign-key-safe seed data. Its callers
are humans, CI pipelines, and LLM agents equally (see docs/product-strategy-notes.md — the
adoption wedge includes CI fixtures and agent workflows, and the LLM thesis is "LLMs should
call this tool instead of inventing fragile scripts").

A Textual TUI for `inspect` was built ahead of need: it is a read-only viewer, and the
workflow that would justify an interactive app — reviewing and *correcting* column
classifications — does not exist yet. Peer tools in this space (Snaplet, Prisma, Atlas,
Neosync) are CLI + config-file products; none ship a TUI. rough_plan.md listed a TUI as
Post-MVP enhancement #6, and its risk table flagged scope creep as the top project risk.

## Decision

1. Every capability is a CLI verb with plain/JSON output and meaningful exit codes;
   headless operation must always work. `inspect` prints text by default; the TUI is
   explicit opt-in (never the default, never an error on non-TTY).
2. Richness goes into verb output: colour-coded confidence in `--format table`,
   `inspect --explain <table.column>`, and `generate --dry-run` (5 sample rows per
   table, per the design already fixed in rough_plan.md).
3. Classification overrides, when built, live in a config file that `generate` consumes.
   The TUI may then become their optional editor.
4. Until overrides exist, TUI investment is frozen: it ships as-is as a demo-able extra;
   no theme picker, no further polish. TUI-scoped ideas are deferred as "post-overrides".
5. Rejected: making the TUI the default interface; a full Typer→Textual migration; a
   dispatcher menu (unwarranted at two verbs).

## Consequences

- Scripts, CI, and agents get stable text/JSON interfaces they can rely on.
- The existing TUI remains useful demo material at zero ongoing maintenance ambition.
- Near-term effort follows the original plan: generator performance (targets: 10K rows/s
  simple, 5K rows/s with FKs), self-referential FKs, `--dry-run`, low-confidence warnings.
