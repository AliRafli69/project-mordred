# Publication checklist

## What this package changes

- Rewrites the six supplied Phase 2 documents into a concise public baseline through Phase 3.
- Removes administrator names, hostnames, private addresses/subnets, interface inventory, raw logs, transient disk/temperature readings, and personal network details.
- Retains relevant architecture, security principles, decision IDs, model configuration, and measured test results.
- Supersedes the old Telegram direction with the browser-chatbot and RAG roadmap.
- Adds a README, ignore rules, Phase 3 validation record, and Postman publication notes.

The original archive is not part of the public package. No API token, model weight, personal note/PDF, or actual Postman export is included.

## Before committing

1. Extract this package and copy its contents into the intended repository. Preserve unrelated existing files.
2. If older documents are already in the repository root, reconcile or replace them rather than leaving contradictory copies beside `docs/`.
3. Review the exact staged diff and filenames. Do not add the original archive or this ZIP alongside the extracted files.
4. Check for credentials, private addresses, usernames, saved responses, and screenshots in the entire staged change, not just Markdown.
5. Keep private operational notes and credential storage outside this public documentation tree.

Suggested commit message:

`docs: sanitize project baseline and record phase 3 validation`

## Important limits

`.gitignore` prevents accidental addition of matching untracked paths; it does not remove already tracked files or clean Git history. If a real credential was ever committed, revoke it and address historical exposure before publication. If old private details are already in history, replacing current files does not erase those revisions.

This package does not create a Git repository, create commits, or push to GitHub. No license is selected on the owner's behalf. The model's name is retained for reproducibility; its weights and any redistribution rights are outside this documentation package.
