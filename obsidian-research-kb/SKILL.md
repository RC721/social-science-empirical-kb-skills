---
name: obsidian-research-kb
description: Render, update, and structurally audit an Obsidian vault used as an empirical social science knowledge base. Use for managed Literature Notes, YAML and Wikilinks, Bases, home pages, research maps, review dashboards, missing-PDF queues, stale-artifact views, and safe preservation of researcher-authored Markdown.
---

# Obsidian Research Knowledge Base

## Required reading

- Read [managed-markdown.md](references/managed-markdown.md) before editing an existing note.
- Read [vault-quality-gates.md](references/vault-quality-gates.md) before reporting a render or audit as complete.
- Use [managed-note-template.md](assets/managed-note-template.md) for new Literature Notes.

## Render safely

1. Treat Obsidian as the live readable knowledge layer from project initialization onward.
2. Modify only machine-owned YAML keys and the block between `research-kb:managed:start` and `research-kb:managed:end`.
3. Preserve all content outside the managed block byte-for-byte.
4. Generate counts and navigation only from the current v2 manifest.
5. Keep explicit links from reviews to Claims, Findings, notes, and evidence locations.
6. Expose pending, needs-review, missing-PDF, failed, and stale states through Bases or generated indexes.
7. Validate legal YAML, unique item keys, Evidence IDs, Wikilinks, filenames, and reciprocal navigation.

Never create Evidence from reader-facing Markdown. Never overwrite a complete note merely to normalize style. Do not delete an Obsidian file solely because the Zotero item disappeared; mark it unavailable or deleted upstream and require review.
