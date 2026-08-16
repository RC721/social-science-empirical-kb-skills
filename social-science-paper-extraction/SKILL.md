---
name: social-science-paper-extraction
description: Extract evidence-grounded research information from social science papers in Zotero, with quantitative-first Study, Variable, Model, and Finding cards and safe fallbacks for qualitative, mixed, bibliometric, review, theoretical, and validation papers. Use when creating or repairing Literature Notes, evidence artifacts, or structured paper extractions.
---

# Social Science Paper Extraction

## Required reading

- Read [evidence-rules.md](references/evidence-rules.md) before reading a paper.
- Read [paper-type-routing.md](references/paper-type-routing.md) after identity and evidence-level checks.
- Read [extraction-contract.md](references/extraction-contract.md) before producing JSON or Markdown.
- Use [literature-note-template.md](assets/literature-note-template.md) for new notes.

## Execute three separate passes

1. **Evidence pass:** read Zotero metadata, Abstract, and available fulltext; create Evidence v2 directly from source text with section, PDF page, table/figure, source hash, and locator quality.
2. **Extraction pass:** fill objective fields only from Evidence. Reliably reconstruct Research Question, Gap, Theory/Mechanism, Contribution, and conceptual measurement when fulltext supports the synthesis.
3. **Note pass:** write a Chinese academic reconstruction with locations and Evidence IDs; do not display long original passages.

For quantitative papers create Study Design, Variable, Model, and Finding cards. Distinguish the paper's actual methods from methods cited in prior literature, main models from robustness models, and empirical results from Discussion interpretation.

## Evidence limits

- `fulltext`: extract all supported fields.
- `abstract-only`: limit content to the Abstract and mark unavailable details `未明确报告`.
- `metadata-only`: maintain identity and PDF status only; create no substantive Finding or Claim.

Use `【根据全文归纳】` when authorship of a reliable synthesis may be confused, `【推断，建议核实】` when meaningful uncertainty remains, and `未明确报告` when evidence cannot determine the field.

Do not force a fixed number of Findings. Preserve effect direction, comparison, estimate, uncertainty, significance, model, scope, and evidence boundary when reported.
