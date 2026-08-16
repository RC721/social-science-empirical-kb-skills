---
name: zotero-corpus-sync
description: Plan and synchronize an empirical-research corpus with Zotero Desktop. Use when Codex must discover a Collection, match items, import approved candidates, detect duplicates or versions, retrieve legal open PDFs, refresh metadata and fulltext state, or build an incremental corpus manifest without unsafe direct database edits.
---

# Zotero Corpus Sync

## Required skills and reading

- Use `zotero:Zotero` as the primary Zotero interface.
- Use `citation-management` only for identity normalization or unresolved duplicate/version work.
- Read [identity-and-write-safety.md](references/identity-and-write-safety.md) before matching or writing.

## Execute

1. Query Zotero again; do not trust an old snapshot when items or PDFs may have changed.
2. Match in order: Zotero item key, normalized DOI, exact normalized title, citekey. Record ambiguity and stop only the affected item.
3. Compare DOI, title, authors, year, attachment lineage, study sample, and publication status to identify duplicates and version families.
4. Produce `zotero_import_plan.json` for all writes. Require one explicit approval per run before applying it.
5. Import only approved records. Use idempotent DOI/title checks and preserve the canonical Zotero key.
6. Seek PDFs only through Zotero, publisher OA links, OpenAlex OA, Unpaywall, institutional repositories, or author-posted lawful copies.
7. Record item version, PDF state, attachment key, indexed pages, fulltext availability, and source snapshot ID.
8. Queue only new or changed items for extraction.

Never write directly to Zotero SQLite. Never enable Sci-Hub, Anna's Archive, or another grey resolver. Do not merge ambiguous versions automatically.

## Output

Update the v2 manifest and task queue. Keep failures item-scoped with explicit codes; retain the last valid artifact when synchronization is incomplete.
