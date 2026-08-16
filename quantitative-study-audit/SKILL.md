---
name: quantitative-study-audit
description: Audit a quantitative social science study's design, estimand, variables, model specification, identification assumptions, diagnostics, robustness, heterogeneity, mechanisms, and causal-language boundary. Use after evidence extraction and before claims or cross-study synthesis; do not use it to invent unreported methods or rewrite author-reported facts.
---

# Quantitative Study Audit

## Required reading

- Read [design-families.md](references/design-families.md) to classify the study and load the relevant checklist.
- Read [causal-language.md](references/causal-language.md) before evaluating causal wording.
- Use [audit-template.json](assets/audit-template.json) for output.

## Audit independently

1. Treat the extraction and Evidence IDs as inputs; return missing evidence to extraction rather than guessing.
2. Identify the estimand, outcome, treatment or exposure, comparison, population, analysis unit, and time structure.
3. Record estimator, fixed/random effects, controls, clustering, weights, interactions, sample restrictions, and missing-data handling.
4. Separate main, robustness, heterogeneity, mechanism, placebo, and diagnostic models.
5. Evaluate design-specific assumptions only when relevant.
6. Preserve the author's claim type separately from the audited identification status.
7. Set `causal_language_gate` to `allowed`, `qualified-only`, or `prohibited`.
8. Mark design judgments `【Codex根据研究设计归纳】` in reader-facing prose.

An observational association remains noncausal even when statistically significant or called an effect by the author. A quasi-experimental design permits qualified causal language only when its identifying assumptions and diagnostics are supported by the paper.

Do not change objective extraction fields. Write discrepancies and concerns to the audit artifact and review queue.
