# State and Human Gates

## Independent status fields

- `ingestion_status`: discovered, screened-in, imported, pdf-ready, unavailable
- `extraction_status`: pending, parsed, extracted, limited, failed
- `review_status`: unreviewed, needs-review, verified, rejected
- `synthesis_status`: pending, integrated, stale, excluded

Do not collapse these dimensions into a single status.

## Required confirmation

Pause for a human decision before:

1. approving a focused or systematic search protocol;
2. resolving boundary screening records;
3. applying each batch Zotero write plan;
4. merging ambiguous DOI, title, citekey, preprint, or published-version identities;
5. declaring a formal conflict, retracting a claim, or promoting a cross-study claim;
6. migrating a schema;
7. upgrading a third-party Skill or production Skill;
8. applying a candidate self-improvement patch;
9. deleting or bulk-renaming files.

## Automatic work after approval

Codex may run approved searches, construct deduplication candidates, locate legal open copies, parse PDFs, generate evidence/extractions/audits, maintain managed Markdown, create preliminary single-study claims, refresh candidate synthesis, and run quality reports.

## Failure preservation

For every failed item, retain the last valid artifact, write `failure_code`, move review state to `needs-review`, and continue. Never overwrite verified material with a truncated or invalid result.
