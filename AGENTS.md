# AGENTS.md

## Layout

- `src/git_dirty_triage/gitio.py`: bounded Git reads and path handling.
- `classify.py`: worktree and local-only-commit classifications.
- `commit.py`: temporary-index commit construction on the remote tip.
- `report.py`: text and JSON output.
- `cli.py`: argument parsing and fetch behavior.
- `examples/make-demo.sh`: original throwaway repository example.
- `docs/demo/make-repo.sh`: recording fixture; refuses an existing directory.
- `docs/demo/`: VHS setup, tapes and media.
- `public.json`: public export allowlist and repository metadata.

## Commands

Run from the repository root:

```sh
PYTHONPATH=src python3 -m git_dirty_triage --help
python3 -m compileall -q src
fixture="$(mktemp -d /tmp/triage-check.XXXXXX)"
bash docs/demo/make-repo.sh "$fixture/repo"
PYTHONPATH=src python3 -m git_dirty_triage --repo "$fixture/repo/shared"
```

The fixture is the existing smoke example, not an automated test suite.
There is no separate test runner or linter configured. Use a new temporary
repository to exercise classification and commit changes; never the shared checkout.

## Changes

- Keep report and JSON meanings aligned. Summary counts separate tracked paths
  from untracked entries; per-class counts include both.
- Keep untracked directories opaque by default. Count files without hashing them;
  never print or commit an opaque directory through the unpublished-path route.
- `contained` is line membership, not order-aware semantic equivalence. Do not
  claim reordered or repeated lines are equivalent without inspecting them.
- Preserve the failed-fetch warning; cached remote refs are not fresh evidence.
- Respect repo-relative prefixes at the Git scan, not only the final report.
- Keep newline-containing names, symlinks and deletions out of generated commits.
- Binary edits whose remote changed since HEAD require a decision.
- Commit on the remote tip with a temporary index. Never move the user's branch,
  real index or working files, and never push from this command.
- A conflicting ledger is not resolved by line union. Preserve whole entries.

## Shared checkout and release

- Never reset, stash, clean, rebase, force-push, or sweep changes with `git add -A`.
- Do not create a worktree to avoid handling the actual shared state.
- Use new throwaway directories for examples; do not remove an existing target.
- Record with the dedicated headless browser through `docs/demo/record.sh`.
- Keep README.md, README.ko.md, pyproject description and public.json aligned.
- A local commit is not publication. Package uploads and version changes require
  the maintainer's release instruction.
