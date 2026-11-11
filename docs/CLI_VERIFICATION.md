# CLI installation verification — 2026-11-11

Verified with skills@1.8.1 under temporary Node 22 (system Node 20 is incompatible). Local-source command: `npx --yes --package=node@22 --package=skills@1.8.1 skills add <clean-local-folder> --agent codex --copy --yes`.

All three skills were actually copied into an isolated project `.agents/skills/<name>` directory. Each installed `scripts/demo.py` was then executed successfully from the parent project, with bundled examples and scripts resolved correctly. This verifies the official CLI local-source installation path, not GitHub-source download, marketplace indexing or automatic Agent activation.

API installation from a working tree initially failed copying .pytest_cache (the CLI still exited 0). Retrying from the clean release ZIP succeeded; inspect CLI messages and installed files, not exit status alone. Do not distribute caches.

Demo results: structured output showed invalid input, valid supplied candidate and diff; API showed 1 passed, 1 deliberately failed, 2 observed; triage preserved unconfirmed root cause. No independent model performance claim.

The adjacent installation-check.json records the earlier isolated-layout check; this record adds actual CLI validation. VERSION is 0.1.0. Release artifacts and immutable source commits are indexed separately.
