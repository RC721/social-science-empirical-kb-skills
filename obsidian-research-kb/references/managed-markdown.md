# Managed Markdown

Automation may edit only declared machine-managed YAML keys and text between one balanced pair of markers:

```markdown
<!-- research-kb:managed:start -->
...
<!-- research-kb:managed:end -->
```

Everything outside is researcher-owned. On a missing, duplicated, reversed, or nested marker, stop with `human_content_overwrite_risk`; do not repair by rewriting the note. Preserve newline style where practical and produce byte-identical output when inputs are unchanged.

Use stable filenames and explicit Wikilinks. Renaming, merging, or deleting notes is a human gate. Reader-facing text should summarize in Chinese and cite original locations or Evidence IDs; original excerpts belong in evidence artifacts, not mandatory prose blocks.
