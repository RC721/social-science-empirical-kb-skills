from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


def _json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def build_upgrade_report(vault: Path) -> dict:
    """Aggregate migration, corpus, evidence, knowledge-layer, and review state."""
    work = vault / "90_Codex工作区"
    manifest = _json(work / "state" / "corpus_manifest.json", {"records": []})
    records = manifest.get("records", [])
    evidence_levels = Counter(row.get("evidence_level", "unknown") for row in records)
    paper_types = Counter(row.get("paper_type") or "unclassified" for row in records)
    extraction = Counter(row.get("extraction_status", "unknown") for row in records)
    review = Counter(row.get("review_status", "unknown") for row in records)
    identity_review = sorted(row.get("zotero_item_key", "") for row in records if row.get("duplicate_candidates"))

    queue = Counter()
    queue_path = work / "state" / "task_queue.jsonl"
    if queue_path.exists():
        for line in queue_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                queue[json.loads(line).get("task", "unknown")] += 1
            except json.JSONDecodeError:
                queue["invalid"] += 1

    artifacts = 0
    evidence_items = 0
    locator_quality = Counter()
    source_hash_missing = 0
    for path in sorted((work / "evidence").glob("*.json")) if (work / "evidence").exists() else []:
        artifact = _json(path, {})
        if artifact.get("schema_version") != 2:
            continue
        artifacts += 1
        for item in artifact.get("evidence", []):
            evidence_items += 1
            locator_quality[item.get("locator_quality") or "unknown"] += 1
            if item.get("source_hash") in {"", None, "legacy-source-hash-unavailable"}:
                source_hash_missing += 1

    candidate = _json(work / "evals" / "gold" / "candidate-gold-set.json", {"items": []})
    versions = _json(work / "skills" / "_release" / "versions.json", {})
    return {
        "schema_version": 1,
        "corpus": {
            "total": len(records),
            "literature_notes": len(list((vault / "01_文献笔记").glob("*.md"))) if (vault / "01_文献笔记").exists() else 0,
            "evidence_levels": dict(sorted(evidence_levels.items())),
            "paper_types": dict(sorted(paper_types.items())),
            "extraction_status": dict(sorted(extraction.items())),
            "review_status": dict(sorted(review.items())),
        },
        "evidence": {
            "v2_artifacts": artifacts,
            "items": evidence_items,
            "locator_quality": dict(sorted(locator_quality.items())),
            "legacy_source_hash_unavailable": source_hash_missing,
        },
        "queue": dict(sorted(queue.items())),
        "identity_review_keys": identity_review,
        "knowledge_layers": {
            "claims": len(list((vault / "06_学术论断").glob("*.md"))) if (vault / "06_学术论断").exists() else 0,
            "concepts": len(list((vault / "03_概念知识").glob("*.md"))) if (vault / "03_概念知识").exists() else 0,
            "topic_reviews": len(list((vault / "02_主题综述").glob("*.md"))) if (vault / "02_主题综述").exists() else 0,
            "comparison_matrices": len(list((vault / "07_主题比较矩阵").glob("*.md"))) if (vault / "07_主题比较矩阵").exists() else 0,
        },
        "gold_evaluation": {
            "candidate_count": len(candidate.get("items", [])),
            "human_verified_count": 0,
        },
        "backups": len(list((work / "backups").glob("pre-v2-*"))) if (work / "backups").exists() else 0,
        "versions": versions,
    }


def _format_counts(values: dict) -> str:
    return "、".join(f"{key}={value}" for key, value in values.items()) or "无"


def write_upgrade_report(vault: Path, report: dict) -> Path:
    """Write the human-readable and machine-readable upgrade reports."""
    reports = vault / "90_Codex工作区" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    markdown = reports / "社会科学实证研究知识库升级报告.md"
    corpus = report["corpus"]
    evidence = report["evidence"]
    queue = report["queue"]
    layers = report["knowledge_layers"]
    gold = report["gold_evaluation"]
    text = f"""# 社会科学实证研究知识库升级报告

## 已完成的基础迁移

- 总记录：{corpus['total']}
- 现有 Literature Notes：{corpus['literature_notes']}
- 证据等级：{_format_counts(corpus['evidence_levels'])}
- 抽取状态：{_format_counts(corpus['extraction_status'])}
- 评审状态：{_format_counts(corpus['review_status'])}
- Evidence v2 文件：{evidence['v2_artifacts']}，证据条目：{evidence['items']}
- 已生成基线备份：{report['backups']}

## 论文类型与证据定位

- 论文类型：{_format_counts(corpus['paper_types'])}
- 定位质量：{_format_counts(evidence['locator_quality'])}
- 旧证据尚无原始 PDF SHA-256：{evidence['legacy_source_hash_unavailable']}

旧证据仅做字段迁移，未从中文 Literature Note 反向重建。没有可核验 PDF 哈希的旧条目被明确保留为待后续 Zotero 全文复核状态。

## 当前任务队列

- 新文献抽取：{queue.get('extract', 0)}
- 身份冲突待人工确认：{queue.get('resolve-identity', 0)}

疑似重复、预印本或正式版本关系不会自动合并；系统只给出候选并等待人工确认。

## 知识层现状

- 学术论断：{layers['claims']}
- 概念：{layers['concepts']}
- 主题综述：{layers['topic_reviews']}
- 比较矩阵：{layers['comparison_matrices']}

## 黄金评测集

- 分层候选：{gold['candidate_count']}
- 已人工核验：{gold['human_verified_count']}

候选集不等同于金标准。只有研究者逐篇核验后，条目才可标为 `human-verified` 并用于 Skill 晋升。

## 尚需人工门

1. 处理身份冲突候选并确认重复或版本关系。
2. 为无冲突的新记录完成证据边界内抽取。
3. 对 157 篇旧笔记确定机器管理区边界；dry-run 不改动任何原文。
4. 完成 30 篇黄金论文候选的人工核验。
5. 对第三方 Skill 的许可证、权限、commit 和适配偏差逐项审核后再由 candidate 晋升 approved。
"""
    markdown.write_text(text, encoding="utf-8")
    (reports / "社会科学实证研究知识库升级报告.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return markdown
