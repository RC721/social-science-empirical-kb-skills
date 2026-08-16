# Identity and Write Safety

## Identity resolution

Match in this order while retaining all signals: Zotero item key, normalized DOI, other stable identifiers, citekey, normalized title plus authors and year. A conflicting item key or DOI is never silently repaired. Record preprint, accepted manuscript, report, and version-of-record relations separately from duplicate status.

## Authority

Zotero metadata, Collection membership, item version, and attachment state are authoritative for the local corpus. Validate that a PDF belongs to its parent item using title, authors, DOI, and first-page information before extraction.

## Import plan

All writes begin as a stable `zotero_import_plan.json` containing action, target collection, proposed metadata, source provenance, duplicate candidates, attachment source, and risk flags. Apply only after one human approval for that batch. Log result item keys and versions.

## PDF policy

Use Zotero's official find-full-text behavior, publisher open copies, OpenAlex OA, Unpaywall, and institutional repositories. Never use shadow libraries or uncertain downloads. A missing legal PDF is an availability state, not permission to infer full-text fields.

## Incremental synchronization

Compare Zotero item version and attachment SHA-256 with the manifest. New, modified, removed-from-collection, duplicate, and version-related records become explicit queue tasks. Never delete local knowledge merely because an item temporarily disappears from a snapshot.
