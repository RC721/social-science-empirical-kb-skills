# Extraction Contract

## Pass 1: identity and structure

Confirm item key, DOI, citekey, title, authors, year, journal, document type, evidence level, PDF identity, and major sections.

## Pass 2: evidence and cards

Extract paper-specific Research Question, explicit and synthesized Gap, theory and mechanism, Study Design Card, Variable Cards, Model Cards, Finding Cards, contributions, author limitations, and relevant locations. Objective fields must be directly reported. Academic summaries must remain faithful to the full text.

Study Design records object, unit, population, sampling frame, eligibility, sample size, time, region, sources, missingness, weights, and design. Variable records concept, role, operational definition, data field, scale, unit, transformation, time reference, source, and validity. Model records purpose, variables, estimator, effects, clustering, weights, interactions, restrictions, assumptions, and diagnostics. Finding records comparison, direction, magnitude, uncertainty, model, sample, robustness, heterogeneity, mechanism status, causal boundary, and Evidence IDs.

## Pass 3: validate and render

Check numerical direction, sample and model consistency, locator existence, evidence level, and unsupported causal language. Save structured JSON before updating the managed Markdown. Preserve high-quality verified content unless evidence supports a correction.
