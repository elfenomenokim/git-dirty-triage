# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses `MAJOR.MINOR.PATCH`.

## [0.1.3] - 2026-11-18

### Fixed

- `--json` escapes every non-ASCII byte in a path, so a checkout that holds a filename Git stored
  as invalid UTF-8 still prints parseable UTF-8 JSON. `--print-unpublished` keeps writing the exact
  bytes.
- `examples/make-demo.sh` refuses an existing target directory instead of deleting it, as
  `docs/demo/make-repo.sh` already did.
- `examples/make-demo.sh` creates the bare remote with `--initial-branch=main`, so on a Git without
  `init.defaultBranch` the clones check out `main` and the fixture holds tracked modifications
  instead of only untracked files.

## [0.1.2] - 2026-11-18

### Fixed

- An edit introduced by an unpublished merge commit appears in `--ahead`, so
  `--commit-unpublished` no longer builds an incomplete commit.
- A filename that begins with a double quote no longer stops the whole classification.
- `--prefix .` and `--prefix ./src` select paths; the prefix is normalised once for the Git scan
  and the report.
- Committed working bytes go through the path's clean filter and line-ending normalisation, as
  `git add` would.

## [0.1.1] - 2026-11-18

### Changed

- Documentation release: the README, the Korean README, the demo recording and the social preview
  were rewritten, and the version moved with them. No behaviour change.

## [0.1.0] - 2026-11-17

### Added

- Classification of every changed path: identical, stale, contained, new, clean, conflicting,
  deleted, untracked file and untracked directory.
- Text and `--json` reports, `--print-unpublished`, `--prefix`, `--ahead`, `--no-fetch` and the
  three `--untracked` modes.
- `--commit-unpublished -m MESSAGE` builds a commit on the remote tip through a temporary index;
  it never pushes.
- Installs as `git-dirty-triage` and as `git dirty-triage`.
