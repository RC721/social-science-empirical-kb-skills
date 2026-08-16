# Workflow Contract

## Authority order

1. Zotero item metadata and attachment state define bibliographic identity.
2. PDF, Abstract, and Metadata channels define the evidence boundary.
3. Evidence artifacts preserve source text and locators.
4. Structured extraction and audit artifacts interpret the evidence.
5. Obsidian Markdown presents Chinese scholarly summaries and researcher-authored notes.

Never use a downstream note to manufacture upstream evidence.

## State transitions

Process a paper through identity, availability, extraction, review, synthesis, and rendering. Use the four independent state fields in the manifest. A failure in one paper must not stop the batch. Keep the last valid artifact when a replacement fails validation.

## Standard run

1. Read project config, manifest, Zotero snapshot, dependency graph, and queue.
2. Detect changed item versions and PDF hashes.
3. Create stable, deduplicated tasks in item-key order.
4. Process no more than the configured batch size, normally 10.
5. Validate artifacts before replacing earlier valid output.
6. Mark affected downstream nodes stale.
7. Render only machine-managed fields and blocks.
8. Audit structure, semantics, evidence, links, and idempotency.

## Data ownership

- Runtime owns JSON state, run logs, generated reports, declared YAML fields, and managed Markdown blocks.
- The researcher owns text outside managed blocks.
- Skills make scholarly judgments; the runtime performs identity matching, hashing, state transitions, validation, stable ordering, and file production.

## Safe degradation

- Full text unavailable: remain abstract-only or metadata-only.
- Locator unstable: use section plus table/figure plus a short original excerpt and set `locator_quality: partial`.
- Design unclear: set `design_identification_status: unclear` and prohibit causal wording.
- Skill or data source unavailable: record a failure code and continue other independent tasks.
