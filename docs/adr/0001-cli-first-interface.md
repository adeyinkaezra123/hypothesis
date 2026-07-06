# ADR 0001: CLI-first interface; TUI parked until classification overrides

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
The project has no active users yet, so breaking changes are cheap and there is no
pressure to ship the TUI for continuity reasons.

## Decision

1. Every capability is a CLI verb with plain/JSON output and meaningful exit codes;
   headless operation must always work. `inspect` prints text by default.
2. Richness goes into verb output: colour-coded confidence in `--format table`,
   `inspect --explain <table.column>`, and `generate --dry-run` (5 sample rows per
   table, per the design already fixed in rough_plan.md).
3. Classification overrides, when built, live in a config file that `generate` consumes.
   The TUI may then become their optional editor.
4. The existing TUI (PR #8) is **parked, not merged**: the PR stays open as a preserved
   prototype, `textual` stays out of the shipped dependency set, and no further TUI work
   happens (no theme picker, no polish). Its UX lessons — scannable confidence, the
   classification drill-down — are ported into plain CLI output instead. The TUI is
   revisited only when classification overrides give it a real job.
5. Rejected: making the TUI the default interface; a full Typer→Textual migration; a
   dispatcher menu (unwarranted at two verbs); deleting the TUI branch (parking is free).

## Consequences

- Scripts, CI, and agents get stable text/JSON interfaces; shipped dependencies stay CLI-only.
- The TUI branch remains a head start for a future overrides editor at zero carrying cost —
  no runtime dependency, no CI snapshot maintenance.
- Near-term effort follows the original plan: generator performance (targets: 10K rows/s
  simple, 5K rows/s with FKs), self-referential FKs, `--dry-run`, low-confidence warnings.
