# git-dirty-triage

[한국어](https://github.com/elfenomenokim/git-dirty-triage/blob/main/README.ko.md)

Tell which modified files in a lagging checkout are really unpublished.

```console
$ git-dirty-triage
checkout is 7 commits behind origin/main
5 changed tracked files: 3 already published, 1 unpublished, 1 needs a decision · 3 untracked entries (1 already on the remote)
      2  identical         same bytes as the remote
      1  stale             an earlier published version of the remote file
      1  contained         the remote already holds every line
      1  new               not on the remote
      1  differs_clean     unpublished edit, merges cleanly
      1  differs_conflict  needs a decision, conflicting lines
      1  untracked_dir     untracked directory, not expanded
        differs_conflict     0 min ago  conflict.txt  1 unique line(s)
        differs_clean        0 min ago  merge.txt  1 unique line(s)
        untracked_dir                  build/  3 file(s)
        new                  0 min ago  new.txt
```

## Why

Several agents or sessions share one checkout. When one of them publishes, it builds a commit on top of the remote tip and pushes; it does not fast-forward the shared checkout, because other sessions are editing files there at that moment. The branch lags on purpose, and `git status` keeps listing work that is already on the remote.

That listing is not harmless. A later "commit everything and push" builds on the stale local HEAD, collides with the remote's newer version of the same file, and the conflict is not in anyone's edit — it is in the publication.

`git status` cannot tell you which modified files carry something new: it compares the working tree with the local index, never with the remote. This tool compares every modified path with the remote tip and answers the real question per path.

- The bytes equal the remote file: the work is published; nothing to do.
- The bytes equal an earlier published version: also published.
- Every line already exists in the remote file: nothing unique.
- The bytes are not on the remote: unpublished.

Untracked trees make that list worse. A build output directory is thousands of files nobody edited, and expanding it buries the handful of real changes. By default git lists an untracked directory as one `build/` row, and this tool keeps it that way: one row, no hashing, never committed. Untracked files themselves are still classified, so a file the remote already has counts as published.

Without `--commit-unpublished` the command only reads. That option writes a commit object and a private ref; it still never moves your branch, index or working tree.

## Install

```console
$ pipx install git-dirty-triage     # recommended: isolated, on PATH
$ uvx git-dirty-triage --help       # or run without installing
$ pip install git-dirty-triage      # inside a project
```

Python 3.9 or newer, git 2.x, and no Python dependencies. The installed command is named `git-dirty-triage`, so git also runs it as `git dirty-triage`.

## Usage

### Classify the dirty paths

```console
$ git-dirty-triage
```

It fetches the branch first, then compares. The first line says how far the checkout lags. The second is the count that matters, in two parts separated by `·`: tracked changes in full detail, then untracked entries. The lines below list only the paths that are not already published. `git status` order is kept; a long path is shortened from the left.

The per-class counts under the summary cover every row, untracked files included. The summary line splits tracked changes from untracked entries, so the two views differ when an untracked file is already on the remote.

### Untracked paths

`-u/--untracked` follows git status:

| Value | An untracked directory | An untracked file |
|---|---|---|
| `normal` (default) | one row, `build/`, with a file count | its own row, classified |
| `all` | expanded: every file gets a row and is classified | its own row, classified |
| `no` | not listed | not listed |

```console
$ git-dirty-triage --prefix build
checkout is 7 commits behind origin/main
1 untracked entry
      1  untracked_dir     untracked directory, not expanded
        untracked_dir                  build/  3 file(s)

$ git-dirty-triage --prefix build --untracked all
checkout is 7 commits behind origin/main
3 untracked entries
      3  new               not on the remote
        new                  0 min ago  build/a.log
        new                  0 min ago  build/cache/b.log
        new                  0 min ago  build/cache/c.log
```

The file count comes from a directory walk; nothing inside an untracked directory is hashed or compared with the remote. `untracked_dir` rows are never printed by `--print-unpublished` and never committed. Use `--untracked all` when you want those files.

### Print only the unpublished paths

```console
$ git-dirty-triage --print-unpublished
merge.txt
new.txt
```

One path per line, ready to pipe. Untracked directories are not printed; untracked files are. Filenames that contain a newline are reported as `skipped` and never printed, so a line is always one path:

```console
$ git-dirty-triage --print-unpublished | while IFS= read -r p; do git add -- "$p"; done
```

### Commit the unpublished paths on top of the remote tip, without pushing

```console
$ git-dirty-triage --commit-unpublished -m "local work"
committed 2 path(s) as 08627b9a8f3ccfca858b1c32dd5bc5ac2135915e on top of origin/main
  ref:  refs/git-dirty-triage/main
  push: not pushed
  next: git push origin 08627b9a8f3ccfca858b1c32dd5bc5ac2135915e:refs/heads/main
```

The commit is built on a temporary index from the remote tip's tree: the parent is `origin/main`, not your HEAD. Edited text uses the three-way merge of your bytes and the remote's, so neither side loses a line; new and binary files are taken whole. Your branch, index and working tree are untouched, and nothing is pushed.

The commit is kept reachable as `refs/git-dirty-triage/<branch>`. Push it when you have looked at it. Until the remote actually has those bytes, a rerun still reports the paths as unpublished on the remote — that is the question the tool answers.

Conflicting paths are never committed. Resolve them where they are edited; a line-union merge of a changelog or a ledger is not a resolution.

### Files touched by local-only commits

`--ahead` answers the other blind spot: a file that was committed locally, never reached the remote, and has a clean working copy. The dirty scan cannot see it.

```console
$ git-dirty-triage --ahead
checkout is 7 commits behind origin/main
1 path touched by local-only commits: 0 already published, 1 unpublished, 0 need a decision
      1  new               not on the remote
        new                  0 min ago  notes.txt
```

The three-way base is the merge-base blob instead of `HEAD`. A path the remote deleted is not brought back, and a version the remote once held counts as `stale`. `--ahead` reads commit contents, so `--untracked` does not apply.

### One directory or file

```console
$ git-dirty-triage --prefix src --prefix README.md
```

`--prefix` limits the listing itself, not only the report, so a unit costs what its own paths cost. Prefixes are repo-relative.

### Machine-readable output

```console
$ git-dirty-triage --json
{"repo": "/tmp/demo/shared", "ref": "origin/main", "behind": 7, "mode": "worktree",
 "counts": {"identical": 2, "stale": 1, "contained": 1, "new": 1, "differs_clean": 1,
            "differs_conflict": 1, "untracked_dir": 1},
 "summary": {"paths": 8,
             "tracked": {"paths": 5, "published": 3, "unpublished": 1, "decide": 1, "deleted": 0, "skipped": 0},
             "untracked": {"entries": 3, "published": 1}},
 "paths": [{"path": "conflict.txt", "class": "differs_conflict", "age_min": 0,
            "reason": "1 unique line(s)", "untracked": false, "files": null}, …]}
```

(Shown wrapped and shortened; the command prints one line.)

Every row carries `untracked` and `files`; `files` is the count on an `untracked_dir` row and `null` elsewhere.

`--commit-unpublished --json` prints a receipt instead: `status`, `commit`, `parent`, `ref`, `files`, `paths`, `pushed` and the `push` command, or `{"status": "nothing_to_commit"}`.

### Exit status

`0` means the report was printed, even when it reports unpublished or conflicting paths — the report is data. `2` means a usage or git error. With `--commit-unpublished`, `0` also covers `nothing to commit`.

## How it decides

| Class | Working bytes against the remote tip | Unpublished? |
|---|---|---|
| `identical` | same blob as remote | no |
| `stale` | equal to an earlier published version of the path | no |
| `contained` | every non-blank line already exists in the remote file | no |
| `new` | the remote has no file at this path | yes |
| `differs_clean` | unique lines, and a three-way merge with `HEAD` as base is clean | yes |
| `differs_conflict` | unique lines, and the same merge conflicts | no — a decision |
| `differs_binary` | binary, and the remote blob is unchanged since `HEAD` | yes, whole file |
| `deleted` | removed in the working tree | reported only |
| `untracked_dir` | untracked directory under `--untracked normal` | one row; never hashed, printed or committed |
| `skipped` | not a plain file (symlink, path with a newline) | reported only |

A clean merge whose result equals the remote bytes is `contained`: the path only lags.

The cost is one batched `hash-object` pass and one `ls-tree` per side. Per-path history is read only for a path that really differs. A 38,925-path checkout was classified in 107 seconds on an Apple-silicon Mac (Python 3.12, warm cache).

## A real example

The output at the top of this page comes from `examples/make-demo.sh`, which builds a throwaway remote and two clones in a temp directory: `peer` publishes seven commits, `shared` lags and edits the same five files plus one new file, one untracked copy of a published file and an untracked `build/` tree.

```console
$ bash examples/make-demo.sh
demo repo: /tmp/git-dirty-triage-demo/shared
$ cd /tmp/git-dirty-triage-demo/shared && git-dirty-triage
```

## When you do not need it

- **Each agent has its own clone or worktree.** Every checkout then tracks the remote, and `git status` is already the truth.
- **The checkout is up to date with the remote.** Same reason.
- **A single writer, no concurrent publication.** Nothing is published behind your back.
- **You want to know whether two branches will merge.** Use `git merge-tree` or `git range-diff`; this tool judges one working tree against one remote branch.

You need it when a checkout is deliberately behind and still has edits — the state a shared multi-agent checkout ends up in.

## Limits

- **The answer describes the last fetch.** The command fetches by default and prints a warning when the fetch fails, then compares with what is already fetched. `--no-fetch` skips the fetch without a notice.
- **Files, not trees.** Directories are not classified; a rename appears as a delete plus a new file. Deleted and skipped paths are reported and never committed.
- **"Unpublished" is not "wanted".** A cleanly merging edit is unpublished by definition; deciding whether it belongs in a commit is yours.
- **Binary files are all-or-nothing**, and only when the remote copy has not changed since HEAD; otherwise the path needs a decision.
- **A committed edit is not your working file.** For `differs_clean` the commit holds the three-way merge, which can differ from the bytes on disk. Your working tree is left as it was.
- **Untracked directories stay opaque by default.** Their file count comes from a directory walk; nothing inside is hashed or compared with the remote. `--untracked all` expands them, which is expensive on a large build tree and is the only way to see, print or commit their files.
- **`--ahead` needs a merge-base.** A depth-1 shallow clone has none.
- **Empty repositories are not supported**; there is no remote tip to compare with.
- **Tested on macOS (Apple silicon, Python 3.12).** The code uses only the standard library and `git`; Linux and Windows are untested — reports welcome.
- **Very large dirty sets** cost one `cat-file` and one `log` per genuinely differing file; only the identical and new paths are cheap.

There is no configuration file and no environment variable. Every default is a flag: `--repo`, `--remote`, `--branch`, `--untracked`.

## Agents

If you are an AI agent asked to publish work from a shared checkout, read [AGENTS.md](https://github.com/elfenomenokim/git-dirty-triage/blob/main/AGENTS.md). The Claude Code skill lives in [`skill/git-dirty-triage/SKILL.md`](https://github.com/elfenomenokim/git-dirty-triage/blob/main/skill/git-dirty-triage/SKILL.md); install it by copying that folder to `~/.claude/skills/git-dirty-triage/`.

## License

MIT — see [LICENSE](https://github.com/elfenomenokim/git-dirty-triage/blob/main/LICENSE).
