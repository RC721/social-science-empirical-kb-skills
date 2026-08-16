---
name: social-science-empirical-kb
description: Orchestrate an auditable Zotero-backed Obsidian knowledge base for empirical social science, especially quantitative research. Use when Codex must initialize, search, ingest, incrementally update, repair, synthesize, or quality-audit a literature corpus while preserving evidence provenance and researcher-authored notes.
---

# Social Science Empirical Knowledge Base

## Purpose

Coordinate specialized Skills and the deterministic runtime. Keep Zotero authoritative for bibliographic identity and PDFs, evidence artifacts authoritative for source support, and Obsidian authoritative for readable research knowledge.

## Required reading

- Read [workflow-contract.md](references/workflow-contract.md) before running a project stage.
- Read [state-and-human-gates.md](references/state-and-human-gates.md) before external writes, schema changes, or conflict resolution.
- Read [third-party-skill-policy.md](references/third-party-skill-policy.md) before adding or upgrading an external Skill.

## Route work

1. Use `$social-science-literature-discovery` for exploratory, focused, or systematic discovery.
2. Use `$zotero-corpus-sync` for Zotero identity, import, PDF state, and incremental synchronization.
3. Use `$social-science-paper-extraction` for evidence artifacts and paper-specific extraction.
4. Use `$quantitative-study-audit` for quantitative design, model, robustness, and causal-language review.
5. Use `$research-knowledge-synthesis` for Findings, Claims, Concepts, matrices, reviews, and questions.
6. Use `$obsidian-research-kb` for managed Markdown, Bases, navigation, and vault checks.
7. Use `$research-kb-evolution` for corrections, evaluations, and Skill improvement proposals.

Do not silently replace a missing child Skill with unsupported generalization. Record the unavailable dependency and use the narrowest safe fallback.

## Execute incrementally

1. Discover the vault, current config, Zotero Collection, manifest, snapshots, evidence, and pending tasks.
2. Run `python scripts/research-kb.py --vault <vault> init` only when the runtime layout is absent.
3. Refresh Zotero state before trusting cached corpus counts.
4. Work in stable batches of 10 papers. Persist task status after every item and batch.
5. Apply `补缺 > 扩充 > 修正 > 重写`. Preserve verified content and researcher-owned Markdown.
6. Propagate upstream changes through the dependency graph; rebuild only stale downstream artifacts.
7. Run structural, semantic, evidence, and idempotency checks before reporting completion.

## Enforce evidence boundaries

- `fulltext`: extract supported study details and Findings with Evidence IDs.
- `abstract-only`: use only information supported by the Abstract; do not invent controls, full model settings, detailed sample construction, or limitations.
- `metadata-only`: maintain identity, version, duplicate, and missing-PDF state only.

Create evidence from Zotero/PDF/Abstract before writing Markdown. Never reconstruct source evidence from a Chinese Literature Note.

## Respect human gates

Require confirmation for a focused/systematic protocol, boundary screening decisions, each Zotero write plan, ambiguous identity/version resolution, conflict/retraction decisions, schema migrations, Skill upgrades, and destructive file operations. Other validated stages may continue automatically.

## Completion

Require valid schemas, unique Zotero keys, stable Evidence IDs, no unsupported objective fields, no causal overstatement, no broken managed blocks, no unapproved Zotero writes, and two identical consecutive deterministic builds. Report remaining semantic review separately from structural pass status.
