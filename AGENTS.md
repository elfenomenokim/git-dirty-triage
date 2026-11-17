# AGENTS.md — git-dirty-triage

Instructions for an AI agent asked to publish work from a checkout that other sessions also use.

## When to use it

Use it when the checkout may hold work that is already on the remote: a shared checkout between agents, a branch that lags because publication does not fast-forward it, or a `git status` list longer than the files you changed.

Do not use it when every agent has its own clone or worktree, or when the checkout already tracks the remote. Then `git status` is already correct.

## Install

```console
$ pipx install git-dirty-triage
```

`uvx git-dirty-triage …` runs it without installing. The command also answers as `git dirty-triage`.

## Use

1. Classify first, before you stage anything:

   ```console
   $ git-dirty-triage --json
   ```

   Read `summary`. `already published` paths carry nothing new. `unpublished` paths do. `decide` paths conflict with the remote and belong to whoever edits them. Untracked entries are counted apart from tracked changes.

   By default an untracked directory is one row with a file count and is never committed. If the new work really is untracked files inside such a directory, add `--untracked all`; otherwise leave it opaque.

2. When your own files are the unpublished ones, either build the commit on the remote tip:

   ```console
   $ git-dirty-triage --commit-unpublished -m "what this unit changes"
   ```

   or take the path list and let your existing publish flow do the commit:

   ```console
   $ git-dirty-triage --print-unpublished
   ```

3. When a file was committed locally and never reached the remote, `--ahead` finds it even though the working copy is clean.

4. Push only after you have looked at the commit. Then rerun the classification: the pushed paths must come back as `identical`, `stale` or `contained`. If they do not, the push did not land — read the remote result instead of trusting a local ref.

5. A `differs_conflict` path is not yours to solve by line union. In a changelog, a ledger or a shared record, entries merge as whole entries; a line-level merge interleaves other sessions' entries and corrupts them.

## Do not

- Do not `git add -A`, `git add .` or `git commit -a` from a classification result. `--print-unpublished` is the exact list.
- Do not expect an untracked directory (`build/`, `dist/`) to be committed; its files are hidden until you pass `--untracked all`, and even then check that they belong in the repository at all.
- Do not use `reset`, `stash`, `clean`, `checkout --`, `rebase` or a force push to make the status look clean. Another session's uncommitted work is in that tree.
- Do not create a worktree in a large shared repository to get a clean tree; the disk cost is real and this pattern avoids conflicts without one.
- Do not report "published" from a local commit. A local commit is not remote completion; check the remote.
- Do not commit `differs_binary` paths whose remote copy changed since HEAD; the tool reports them as a decision for a reason.

## Verify before you claim

1. The command exited 0 and you read its summary line.
2. The commit you pushed exists on the remote branch — fetch it and read the path from the remote, not from your HEAD.
3. Rerunning the classifier no longer reports those paths as unpublished.
