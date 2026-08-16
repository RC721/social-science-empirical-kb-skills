# Third-party Skill Policy

## Admission

Before approval, record repository, immutable commit, license, purpose, adapter, network access, write permissions, known biases, review date, and regression suite in `skills.lock.yaml`. Run security and permission review. Reject packages with unclear licensing or unnecessarily broad writes.

## Adapter rules

- Remove citation-count, journal-rank, author-prestige, and English-only filters as default inclusion criteria.
- Do not allow a discovery Skill to write Zotero directly.
- Do not allow a PDF tool to bypass source provenance.
- Do not allow an evaluation Skill to turn a design judgment into an author statement.
- Return explicit degradation results when a provider is unavailable.

## Versioning

Pin Git commits. Review upgrades in isolation, run the relevant gold and forward suites, then require human promotion. Never follow latest versions automatically.

## Initial roles

Use Zotero for corpus operations; OpenAlex and paper lookup for discovery; citation management for DOI and version checks; PDF inspection for locators; critical-thinking and scholar-evaluation tools for evidence boundaries; statistical tools for model recognition; causal-design tools for identification checks; Obsidian ontology tools for structure; and completion verification for release gates.
