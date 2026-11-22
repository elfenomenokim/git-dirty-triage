# AGENTS.md

## Set up for a user

Goal: in a Git checkout that lags behind its remote, `git-dirty-triage` says which modified files are already published and which carry something new. Nothing here needs the person except which checkout to look at.

1. Check what is present.
   - `git --version` prints 2.x. If not: `brew install git` (macOS) or `sudo apt install git`.
   - `uv --version` prints a version. If not: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then `export PATH="$HOME/.local/bin:$PATH"` (or open a new shell).
2. Install: `uv tool install git-dirty-triage`. It ends with `Installed 1 executable: git-dirty-triage`; `git-dirty-triage --version` prints `git-dirty-triage 0.1.3` or newer. `uv tool update-shell` puts `~/.local/bin` on PATH for later shells. No Python dependencies.
3. Prove it on a throwaway repository pair, never on the user's checkout:
   ```sh
   d=$(mktemp -d); cd $d
   git init -q --bare remote.git -b main; git clone -q remote.git a; git clone -q remote.git b
   (cd a && echo one > f.txt && git add f.txt && git commit -qm one && git push -q origin main)
   (cd b && git pull -q origin main && cd ../a && echo two > f.txt && git commit -qam two && git push -q origin main)
   (cd b && echo local > new.txt && echo edit > f.txt && git-dirty-triage)
   ```
   It prints `checkout is 1 commit behind origin/main`, then a summary that includes `1 needs a decision` and a `new.txt` line marked `new`. Delete `$d` afterwards. (Git needs `user.name` and `user.email` set to commit; set them locally in the scratch repos if it complains.)
4. Real use: from the user's checkout run `git-dirty-triage` (it fetches the remote first; the working tree is not changed). `git-dirty-triage --print-unpublished` lists only files that carry something new. `--commit-unpublished` makes a commit and needs the user's yes first.
5. If it fails, in this order:
   - `git-dirty-triage: command not found`: `~/.local/bin` is not on PATH (step 2).
   - `not a git repository`: run it from inside the checkout or pass `--repo PATH`.
   - A fetch error: no network or no access to the remote; add `--no-fetch` to classify against what is already fetched, and say so.
   - Output says the checkout is not behind: there is nothing to triage; that is a valid result.

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

## Code Review Rules

A change is a real defect when it:

- moves the user's branch, real index or working files, or pushes from the command.
- builds a commit on anything but the remote tip with a temporary index.
- hashes, prints or commits an opaque untracked directory.
- lets a newline-containing name, a symlink or a deletion into a generated commit.
- drops the failed-fetch warning, or treats cached remote refs as fresh evidence.
- mixes tracked paths with untracked entries in the summary counts, or makes per-class counts disagree with the report.
- describes `contained` as order-aware equivalence, or resolves a conflicting ledger by line union.
- applies a repo-relative prefix only in the report and not in the Git scan.

Not defects: wording, formatting, comment style, requested extra tests, or a renamed helper.
