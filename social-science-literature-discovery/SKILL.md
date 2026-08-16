---
name: social-science-literature-discovery
description: Discover, deduplicate, screen, and document social science literature across open scholarly indexes and authorized domain databases. Use for exploratory scoping, focused topic searches, systematic searches, citation chasing, search updates, candidate ranking, and reproducible Zotero import planning.
---

# Social Science Literature Discovery

## Required reading

- Read [search-protocol.md](references/search-protocol.md) before designing queries or claiming coverage.
- Read [ranking-and-screening.md](references/ranking-and-screening.md) before ranking or excluding candidates.
- Use [search-protocol-template.yaml](assets/search-protocol-template.yaml) for every run.

## Select a mode

- `exploratory`: map concepts and candidate literatures; never claim completeness.
- `focused`: search multiple sources, chase citations, and assess saturation; confirm the protocol before screening.
- `systematic`: preserve exact queries, dates, databases, decisions, exclusion reasons, and flow counts; confirm the protocol before execution.

## Execute

1. Translate the research question into population/object, exposure or explanatory concept, outcome, mechanism, context, measurement terms, and study-design terms.
2. Separate theoretical terms from operational measures and data-field names.
3. Search OpenAlex, Semantic Scholar, Crossref, and authorized domain sources. Record unavailable sources rather than implying coverage.
4. Add backward and forward citation candidates and recent related work.
5. Normalize DOI, title, authors, year, and version family before deduplication.
6. Score topic, object, measurement, method, recency, citation-network position, source status, and model uncertainty separately.
7. Send uncertain inclusion cases to human review. Preserve every systematic exclusion reason.
8. Generate a Zotero import plan; do not write to Zotero directly.

Never use citation count, journal rank, institution, or author prestige as an automatic inclusion or quality rule. Do not exclude new, regional, non-English, replication, or null-result studies solely because they lack citations.

## Output contract

Create `search_protocol.yaml`, `queries.json`, `candidates.jsonl`, `deduplication.json`, `screening_log.jsonl`, `coverage_report.md`, and `zotero_import_plan.json` under one immutable `run_id`.
