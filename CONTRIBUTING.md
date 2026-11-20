# Contributing to git-dirty-triage

Fixes and reports are welcome. You do not need to ask before opening a pull request for a bug fix.

## Before you start

- **A wrong classification:** open an
  [issue](https://github.com/elfenomenokim/git-dirty-triage/issues/new/choose) with the report, the
  `--json` output, your Git version, and the commands that built the repository. A throwaway
  repository that reproduces it is the most useful evidence.
- **A change to what counts as unpublished:** open an issue first. A wrong classification either
  loses an edit or publishes one.
- **A security problem:** do not open a public issue. See [SECURITY.md](SECURITY.md).

## Set up

```sh
git clone https://github.com/elfenomenokim/git-dirty-triage
cd git-dirty-triage
python3 -m compileall -q src
fixture="$(mktemp -d /tmp/triage-check.XXXXXX)"
bash docs/demo/make-repo.sh "$fixture/repo"
PYTHONPATH=src python3 -m git_dirty_triage --repo "$fixture/repo/shared"
```

There is no separate test runner; the fixture is the smoke example. Exercise a change in a new
temporary repository, never in the checkout you are working in.

## Rules a patch must keep

- Keep the report and the JSON meanings aligned. A summary count and a per-class count mean
  different things.
- Keep untracked directories opaque by default: count the files, do not hash them, and never
  commit one through the unpublished-path route.
- `contained` is line membership, not semantic equality.
- Respect repo-relative prefixes at the Git scan, not only in the final report.
- Commit through a temporary index on the remote tip, with the same clean filters and line endings
  that `git add` would apply.

## What a good patch has

- **A fixture or a script** that shows the bug before the change and the right answer after it.
- **A line under Unreleased** in [CHANGELOG.md](CHANGELOG.md) when a user will notice.
- **The platforms you did not test** written in the pull request. The `tests` workflow runs the compile and fixture smoke check on Ubuntu, macOS and Windows with Python 3.9 and 3.13.

## Review

Every pull request runs an automatic DeepSeek review. Ask for another pass with `@codex review` or
`@claude review` in a comment. If a finding looks wrong, say why in the pull request.

## Licence

Contributions are licensed under the MIT licence in [LICENSE](LICENSE).
