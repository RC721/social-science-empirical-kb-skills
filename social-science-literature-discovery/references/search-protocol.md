# Search Protocol

## Translate the research need

Build separate concept clusters for population or research object, outcome, exposure or explanatory concept, mechanism, measurement, geography, period, and study design. Expand synonyms in the languages relevant to the project. Preserve both natural-language questions and database-specific query strings.

## Modes

- `exploratory`: rapid landscape scan; record sources and date but make no completeness claim.
- `focused`: query multiple databases, follow backward and forward citations, search key authors or measures, and examine saturation. A human approves the protocol.
- `systematic`: additionally freeze exact strings, interfaces, time limits, eligibility criteria, screening reasons, deduplication decisions, and PRISMA counts. A human approves protocol and boundary records.

## Sources

Use OpenAlex, Semantic Scholar, Crossref, and suitable discipline or regional databases through adapters. Search references and citing works for seed papers. Treat metadata coverage and API limits as explicit search limitations.

## Reproducibility

Every run must produce `search_protocol.yaml`, `queries.json`, `candidates.jsonl`, `deduplication.json`, `screening_log.jsonl`, `coverage_report.md`, and `zotero_import_plan.json`. Record query time in UTC, provider, parameters, result count, pagination, and errors.
