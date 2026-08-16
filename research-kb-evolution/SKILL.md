---
name: research-kb-evolution
description: Improve a research knowledge-base Skill suite from human corrections, failure clusters, gold-paper evaluations, and third-party dependency changes. Use when recording corrections, diagnosing repeated extraction errors, proposing schema or Skill patches, running regression and forward tests, promoting a version, or rolling back a degraded release.
---

# Research Knowledge Base Evolution

## Required reading

- Read [correction-and-promotion.md](references/correction-and-promotion.md) before generalizing a correction or changing a production Skill.
- Read [gold-evaluation.md](references/gold-evaluation.md) before running or interpreting evaluations.

## Execute a governed improvement loop

1. Record each correction with item, artifact, field, evidence, root cause, affected Skill, and reusable-rule assessment.
2. Keep paper-specific exceptions as cases; generalize only repeated, evidence-backed failure patterns.
3. Draft a candidate patch in the independent Skill Git repository.
4. Add a failing regression test before changing runtime behavior.
5. Run unit, contract, gold-paper, trigger-routing, idempotency, and fresh-context forward tests.
6. Compare the candidate against the last approved release and report improvements and regressions.
7. Require human approval before promoting a Skill, schema, adapter, or dependency version.
8. Pin the approved version and retain a rollback artifact.

Never let a production Skill rewrite itself and activate the change in one run. Never optimize only for fluent prose; critical numerical, identity, evidence, and causal-boundary errors are release blockers.
