# Publication checklist

## Public repository scope

- The public documentation covers the project baseline through Phase 5 without deployment-specific values.
- It retains architecture, security principles, decision IDs, model configuration, and verified test results.
- Telegram is the first user-facing adapter; its real bot token and allowed user IDs belong only in ignored local configuration.

No API token, private prompt, model weight, personal note/PDF, raw log, or actual Postman export belongs in this repository.

## Before committing

1. Review the exact staged and unstaged diff, plus untracked files.
2. Check the whole proposed change for credentials, private addresses, usernames, Telegram IDs, saved responses, screenshots, and private prompt text. Inspect code and configuration examples as well as Markdown.
3. Confirm `.env` and `prompts/system_prompt.private.txt` remain ignored and outside Docker build context; do not print their contents.
4. Run the automated suite, validate Compose, and record any live checks separately from automated checks.
5. Keep private operational notes and credential storage outside this public documentation tree. Obtain review of the diff and secret-check results before committing or pushing Phase 5.

Suggested Phase 5 commit message:

`feat: add authorized Telegram adapter and phase 5 documentation`

## Important limits

`.gitignore` prevents accidental addition of matching untracked paths; it does not remove already tracked files or clean Git history. If a real credential was ever committed, revoke it and address historical exposure before publication. If old private details are already in history, replacing current files does not erase those revisions.

No license is selected on the owner's behalf. The model's name is retained for reproducibility; its weights and any redistribution rights are outside this documentation package.
