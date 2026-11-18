---
name: git-dirty-triage
description: Tell which modified files in a shared or lagging Git checkout are really unpublished, and commit only those on top of the remote tip without pushing. Use when `git status` in a shared checkout lists work other sessions already published, before a "commit everything" run, or when a local-only commit may not have reached the remote. Do not use when each agent has its own clone or worktree, or when the checkout already tracks the remote.
---

# git-dirty-triage

`git status` compares the working tree with the local index, so in a checkout that lags behind the remote it lists published work as modified. This command compares each modified path with the remote tip and says which ones carry something new.

## Steps

1. Classify before staging anything:

   ```console
   $ git-dirty-triage
   ```

   Read the summary line: already published / unpublished / needs a decision. `--json` gives the same data as one object.

2. Keep your own paths, drop the rest. `identical`, `stale` and `contained` are already on the remote; re-committing them builds on a stale HEAD and collides with the remote.

3. For your own unpublished files, either commit them on the remote tip:

   ```console
   $ git-dirty-triage --commit-unpublished -m "what this unit changes"
   ```

   The parent is the remote tip, not HEAD; the working tree and index are untouched; nothing is pushed. Or take `--print-unpublished` and use your existing publish flow.

4. Look at the commit, push it, then rerun the classification. The paths must come back as already published. A local commit is not remote completion.

5. `differs_conflict` belongs to the session editing that path. Report it; never resolve it by line union.

## Notes

- `--ahead` finds files touched by local-only commits, which the dirty scan cannot see.
- Untracked handling follows git status: `-u normal` (default) shows an untracked directory as one row with a file count and never commits it, `-u all` expands every file, `-u no` skips them. Add `--untracked all` when the unit really is new files under an untracked directory.
- `--prefix src` limits the listing and the cost, not just the report.
- `--remote` and `--branch` replace the hardcoded `origin/main`; by default the remote's own default branch is used.
- Without network the fetch fails and the command says so; `--no-fetch` skips the fetch.
- The command never moves your branch, index or working tree. It creates no tags and pushes nothing.
