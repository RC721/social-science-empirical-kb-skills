# Evidence Rules

## Source hierarchy

Create evidence directly from the matched PDF, Abstract, or Metadata. Do not reconstruct an excerpt from a Literature Note, topic review, claim, or prior Codex summary.

## Evidence v2

Each record needs `evidence_id`, `evidence_type`, `source_channel`, `section`, `pdf_page`, `table_or_figure`, `original_text`, `locator_quality`, `source_hash`, and `extracted_at`. Evidence IDs must be deterministic from source hash, type, locator, and original text.

## Location

Label recovered attachment pagination as `PDF p.N`. Prefer section plus page plus table or figure. If page recovery is unstable, keep section, table/figure, and a short excerpt and set `locator_quality: partial`. Never present a guessed printed page as a PDF page.

## Evidence levels

- `fulltext`: extract only information found in the accessible paper; associate every Finding and critical number with Evidence IDs.
- `abstract-only`: do not populate unreported controls, complete model settings, sample construction, detailed limitations, or results beyond the Abstract.
- `metadata-only`: populate identity and availability only.

## Statement provenance

Separate author statements, reliable full-text synthesis, and Codex methodological judgment. Use `未明确报告` where the source does not support an answer. Use `【推断，建议核实】` only for useful but genuinely uncertain interpretation.
