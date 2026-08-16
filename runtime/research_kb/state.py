from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path


WORKSPACE_DIRS = (
    "config/domains",
    "config/schemas",
    "state",
    "search_runs",
    "zotero_snapshots",
    "evidence",
    "extractions",
    "audits",
    "runs",
    "feedback",
    "evals/gold",
    "reports",
)


def initialize_workspace(vault: Path, collection_key: str = "", domain: str = "general") -> dict[str, Path]:
    """Create the deterministic runtime layout without overwriting user configuration."""
    work = vault / "90_Codex工作区"
    for relative in WORKSPACE_DIRS:
        (work / relative).mkdir(parents=True, exist_ok=True)

    config = work / "config" / "research-kb.yaml"
    skills_lock = work / "config" / "skills.lock.yaml"
    manifest_schema = work / "config" / "schemas" / "corpus-manifest-v2.schema.json"
    evidence_schema = work / "config" / "schemas" / "evidence-v2.schema.json"
    extraction_schema = work / "config" / "schemas" / "extraction-v2.schema.json"
    audit_schema = work / "config" / "schemas" / "quantitative-audit-v1.schema.json"
    correction_schema = work / "config" / "schemas" / "correction-v1.schema.json"
    policy_domain = work / "config" / "domains" / "policy-citation.yaml"
    corrections = work / "feedback" / "corrections.jsonl"
    queue = work / "state" / "task_queue.jsonl"
    graph = work / "state" / "dependency_graph.json"

    if not config.exists():
        config.write_text(
            "\n".join(
                [
                    'schema_version: "2.0.0"',
                    'runtime_version: "0.1.0"',
                    f'collection_key: "{collection_key}"',
                    f'domain: "{domain}"',
                    'output_language: "zh-CN"',
                    'default_search_mode: "focused"',
                    "batch_size: 10",
                    "managed_markdown: true",
                    "allow_non_open_pdf_sources: false",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    if not skills_lock.exists():
        skills_lock.write_text(
            """schema_version: "1.0.0"
skills:
  - skill_id: "zotero:Zotero"
    source_repository: "openai-curated-remote/zotero"
    commit: "plugin-0.1.2+sha256:2053f1c8a7dc93265e9e68d51007627e6111567372057607636c2c74f1ab8f72"
    license: "provider-managed"
    role: "zotero-primary-interface"
    adapter: "zotero"
    status: "approved"
    network_access: "local-first"
    write_permissions: "confirm-per-run"
    known_biases: ""
    reviewed_at: "2026-08-16"
    regression_suite: "zotero-contract"
  - skill_id: "openalex-database"
    source_repository: "K-Dense-AI/scientific-agent-skills"
    commit: "sha256:eeabdfd2023cb84530a2a9eb6eb563b09821368d3a30ad24f137d4a92fd60afe"
    license: "review-required"
    role: "open-literature-discovery"
    adapter: "openalex"
    status: "candidate"
    network_access: "api.openalex.org"
    write_permissions: "none"
    known_biases: "coverage varies by field and language"
    reviewed_at: ""
    regression_suite: "discovery-contract"
  - skill_id: "paper-lookup"
    source_repository: "local-installed-package"
    commit: "sha256:8c17bfaff61ab9195947d0b559846c6941626ca3116f83e2f2b8d4de97b3e7ad"
    license: "review-required"
    role: "multi-source-discovery"
    adapter: "paper-lookup"
    status: "candidate"
    network_access: "academic-providers"
    write_permissions: "none"
    known_biases: "provider coverage differs by discipline and language"
    reviewed_at: ""
    regression_suite: "discovery-contract"
  - skill_id: "citation-management"
    source_repository: "local-installed-package"
    commit: "sha256:6ae983b5dc72d765d62b032dd662ef53a9d9cfd751eaf7c47f213ddd0aa18752"
    license: "review-required"
    role: "identifier-and-version-verification"
    adapter: "citation-identity"
    status: "candidate"
    network_access: "bibliographic-providers"
    write_permissions: "none"
    known_biases: "identifier metadata can contain version conflicts"
    reviewed_at: ""
    regression_suite: "identity-contract"
  - skill_id: "pdf:pdf"
    source_repository: "openai-primary-runtime/pdf"
    commit: "runtime-26.813.12317+sha256:1cf6f39e3a444342b137435647e21a800780bc377e70fe0684021e50a60fefda"
    license: "provider-managed"
    role: "pdf-page-table-figure-inspection"
    adapter: "pdf-inspection"
    status: "approved"
    network_access: "none"
    write_permissions: "workspace-only"
    known_biases: "OCR and page recovery can fail on scans"
    reviewed_at: "2026-08-16"
    regression_suite: "pdf-locator-contract"
  - skill_id: "scientific-critical-thinking"
    source_repository: "local-installed-package"
    commit: "sha256:097662636ad6f3252855c24b3e9384a7cea33d72ad21f89140b87c8058c86718"
    license: "review-required"
    role: "evidence-boundary-review"
    adapter: "critical-thinking"
    status: "candidate"
    network_access: "none"
    write_permissions: "none"
    known_biases: "judgments require paper-specific evidence"
    reviewed_at: ""
    regression_suite: "semantic-audit-contract"
  - skill_id: "scholar-evaluation"
    source_repository: "local-installed-package"
    commit: "sha256:ea58f38df5c4d9843ad7e013d164d3db7351b04b629897c9c0474a213e40d13c"
    license: "review-required"
    role: "study-quality-evaluation"
    adapter: "study-quality"
    status: "candidate"
    network_access: "optional"
    write_permissions: "none"
    known_biases: "prestige indicators must not control inclusion"
    reviewed_at: ""
    regression_suite: "semantic-audit-contract"
  - skill_id: "statistical-analysis"
    source_repository: "local-installed-package"
    commit: "sha256:10844786a2b5c71fbe38fbac73745123b84e6c51ec06dfb6a2e1e19e9c7460a2"
    license: "review-required"
    role: "statistical-method-recognition"
    adapter: "statistics"
    status: "candidate"
    network_access: "none"
    write_permissions: "workspace-only"
    known_biases: "generic guidance cannot replace reported model evidence"
    reviewed_at: ""
    regression_suite: "quantitative-audit-contract"
  - skill_id: "statsmodels"
    source_repository: "local-installed-package"
    commit: "sha256:aa1a672b7857ce58deb9063f9727dec8959ca01541ff8c5d551c1c3cee0bd936"
    license: "review-required"
    role: "model-specification-reference"
    adapter: "statsmodels"
    status: "candidate"
    network_access: "none"
    write_permissions: "workspace-only"
    known_biases: "software defaults may differ from the paper"
    reviewed_at: ""
    regression_suite: "quantitative-audit-contract"
  - skill_id: "everyday-causal-skills"
    source_repository: "RobsonTigre/everyday-causal-skills"
    commit: "not-installed"
    license: "review-required"
    role: "causal-method-audit"
    adapter: "causal-audit"
    status: "candidate"
    network_access: "none"
    write_permissions: "none"
    known_biases: "method guidance requires paper-specific evidence"
    reviewed_at: ""
    regression_suite: "quantitative-audit-contract"
  - skill_id: "SLR-Engine"
    source_repository: "candidate-not-installed"
    commit: "not-installed"
    license: "review-required"
    role: "systematic-review-workflow"
    adapter: "systematic-search"
    status: "candidate"
    network_access: "review-required"
    write_permissions: "none"
    known_biases: "must preserve provider-specific reproducibility"
    reviewed_at: ""
    regression_suite: "systematic-discovery-contract"
  - skill_id: "paper-search-pro"
    source_repository: "candidate-not-installed"
    commit: "not-installed"
    license: "review-required"
    role: "multilingual-literature-discovery"
    adapter: "paper-search-pro"
    status: "candidate"
    network_access: "review-required"
    write_permissions: "none"
    known_biases: "language and database coverage require measurement"
    reviewed_at: ""
    regression_suite: "multilingual-discovery-contract"
  - skill_id: "obsidian-ontology-sync"
    source_repository: "local-installed-package"
    commit: "version-1.0.1+sha256:851cc44393e9df232b1552e2b00d3c63d32566ea52736924f69f3d71718aff0c"
    license: "review-required"
    role: "knowledge-structure-check"
    adapter: "obsidian-ontology"
    status: "candidate"
    network_access: "none"
    write_permissions: "workspace-only"
    known_biases: "semantic similarity is candidate evidence only"
    reviewed_at: ""
    regression_suite: "obsidian-contract"
  - skill_id: "verification-before-completion"
    source_repository: "local-installed-package"
    commit: "sha256:c35ac975d145f74d9f3668c1b035a3754d3c0f4edb491cc80a6a0265cfdf7749"
    license: "review-required"
    role: "release-verification"
    adapter: "release-gate"
    status: "candidate"
    network_access: "none"
    write_permissions: "none"
    known_biases: "command success alone is not semantic validation"
    reviewed_at: ""
    regression_suite: "release-contract"
""",
            encoding="utf-8",
        )
    if not policy_domain.exists():
        policy_domain.write_text(
            """schema_version: "1.0.0"
domain_id: "policy-citation"
display_name: "政策引用与科学—政策知识流动"
topic_concepts:
  - policy citation
  - policy impact
  - knowledge mobilization
  - evidence use
comparison_matrix_fields:
  database:
    - policy_document_definition
    - coverage
    - matching_rule
    - validity
    - bias
  mechanism:
    - outcome
    - explanatory_variable
    - model
    - effect_direction
    - causal_status
  knowledge_flow:
    - nodes
    - path
    - policy_stage
    - timing
  inequality:
    - geographic_scope
    - local_evidence
    - global_north_south_difference
    - conditioning_variables
""",
            encoding="utf-8",
        )
    if not manifest_schema.exists():
        manifest_schema.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "Social Science Corpus Manifest v2",
                    "type": "object",
                    "required": ["schema_version", "records"],
                    "properties": {
                        "schema_version": {"const": 2},
                        "records": {"type": "array", "items": {"type": "object", "required": ["zotero_item_key", "ingestion_status", "extraction_status", "review_status", "synthesis_status"]}},
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if not extraction_schema.exists():
        extraction_schema.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "Social Science Study Extraction v2",
                    "type": "object",
                    "required": ["schema_version", "zotero_item_key", "evidence_level", "study_design", "variables", "models", "findings"],
                    "properties": {
                        "schema_version": {"const": 2},
                        "zotero_item_key": {"type": "string", "minLength": 1},
                        "evidence_level": {"enum": ["fulltext", "abstract-only", "metadata-only"]},
                        "paper_type": {"type": "string"},
                        "study_design": {"type": "object"},
                        "variables": {"type": "array", "items": {"type": "object"}},
                        "models": {"type": "array", "items": {"type": "object"}},
                        "findings": {"type": "array", "items": {"type": "object"}},
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if not evidence_schema.exists():
        evidence_schema.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "Evidence Artifact v2",
                    "type": "object",
                    "required": ["schema_version", "zotero_item_key", "evidence_level", "evidence"],
                    "properties": {
                        "schema_version": {"const": 2},
                        "zotero_item_key": {"type": "string", "minLength": 1},
                        "evidence_level": {"enum": ["fulltext", "abstract-only", "metadata-only"]},
                        "evidence": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["evidence_id", "evidence_type", "source_channel", "section", "pdf_page", "table_or_figure", "original_text", "locator_quality", "source_hash", "extracted_at"],
                            },
                        },
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if not audit_schema.exists():
        audit_schema.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "Quantitative Study Audit v1",
                    "type": "object",
                    "required": ["schema_version", "item_key", "author_claim_type", "design_identification_status", "causal_language_gate"],
                    "properties": {
                        "schema_version": {"const": 1},
                        "author_claim_type": {"enum": ["descriptive", "associational", "causal"]},
                        "design_identification_status": {"enum": ["descriptive", "observational", "quasi-experimental", "experimental", "unclear"]},
                        "causal_language_gate": {"enum": ["allowed", "qualified-only", "prohibited"]},
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if not correction_schema.exists():
        correction_schema.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "Research KB Correction v1",
                    "type": "object",
                    "required": ["correction_id", "item_key", "artifact", "field", "error_type", "old_value", "corrected_value", "root_cause", "affected_skill", "skill_version", "reusable_rule", "reviewed_by", "reviewed_at"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    for path, default in ((corrections, ""), (queue, ""), (graph, "{}\n")):
        if not path.exists():
            path.write_text(default, encoding="utf-8")
    return {
        "workspace": work,
        "config": config,
        "skills_lock": skills_lock,
        "manifest_schema": manifest_schema,
        "evidence_schema": evidence_schema,
        "extraction_schema": extraction_schema,
        "audit_schema": audit_schema,
        "correction_schema": correction_schema,
        "policy_domain": policy_domain,
        "corrections": corrections,
        "queue": queue,
        "dependency_graph": graph,
    }


def build_task_queue(records: list[dict]) -> list[dict]:
    """Build a stable extraction queue, preserving failure review priority."""
    by_key: dict[str, dict] = {}
    for row in records:
        key = row.get("zotero_item_key", "")
        if not key or row.get("extraction_status") not in {"pending", "failed"}:
            continue
        status = "needs-review" if row.get("review_status") == "needs-review" else "pending"
        by_key[key] = {"item_key": key, "task": "extract", "status": status}
    return [by_key[key] for key in sorted(by_key)]


def mark_dependents_stale(graph: dict[str, list[str]], changed: list[str]) -> list[str]:
    """Return the transitive downstream artifacts affected by upstream changes."""
    queue = deque(sorted(changed))
    seen = set(changed)
    affected: set[str] = set()
    while queue:
        current = queue.popleft()
        for dependent in sorted(graph.get(current, [])):
            if dependent in seen:
                continue
            seen.add(dependent)
            affected.add(dependent)
            queue.append(dependent)
    return sorted(affected)


def evidence_id(item_key: str, evidence_type: str, section: str, pdf_page: int | None, table_or_figure: str, original_text: str) -> str:
    """Create a stable evidence ID from source identity and location."""
    payload = "\x1f".join([item_key, evidence_type, section, str(pdf_page or ""), table_or_figure, original_text.strip()])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10].upper()
    return f"{item_key}-E{digest}"


def validate_extraction(extraction: dict, evidence_ids: set[str]) -> list[str]:
    """Validate required extraction structure and evidence support for objective values."""
    errors: list[str] = []
    required = ("schema_version", "zotero_item_key", "evidence_level", "study_design", "variables", "models", "findings")
    for field in required:
        if field not in extraction:
            errors.append(f"missing required field: {field}")
    design = extraction.get("study_design", {})
    for field in ("sample_size", "time_range", "data_sources"):
        value = design.get(field)
        ids = design.get("evidence_ids", [])
        if value not in (None, "", [], "未明确报告") and not ids:
            errors.append(f"study_design.{field} requires evidence_ids")
    for group in ("variables", "models", "findings"):
        for index, item in enumerate(extraction.get(group, [])):
            ids = item.get("evidence_ids", [])
            if not ids:
                errors.append(f"{group}[{index}] requires evidence_ids")
            for value in ids:
                if value not in evidence_ids:
                    errors.append(f"{group}[{index}] references missing evidence_id: {value}")
    for value in design.get("evidence_ids", []):
        if value not in evidence_ids:
            errors.append(f"study_design references missing evidence_id: {value}")
    return errors
