"""Classify each modified path against the remote tip.

Classes, checked in this order:

  identical          working bytes equal the remote file: already published
  stale              working bytes equal an earlier published version of the path: already published
  contained          every non-blank working line already exists in the remote file: nothing unique
  new                not on the remote at all: unpublished
  differs_clean      has unique lines and a three-way merge (base = local HEAD) is clean: unpublished
  differs_conflict   has unique lines and the merge conflicts: needs a decision, never committed
  differs_binary     binary file that differs: unpublished whole only if the remote file is unchanged since HEAD
  deleted            removed in the working tree: reported only
  untracked_dir      untracked directory with --untracked normal: one row, never expanded or committed
  skipped            not a plain file (symlink, path with a newline): reported only

A clean merge that equals the remote bytes is `contained`: the path only lags.

Files are normalized and hashed by path and compared with one ls-tree per side; only a path that really
differs spawns more git calls (`log` + `cat-file --batch-check` for earlier versions, then
`cat-file blob` and `merge-file`).
"""

from __future__ import annotations

import os
import time

from .gitio import (
    count_files,
    dirty_paths,
    hash_files,
    is_text,
    merge_base,
    out,
    published_versions,
    show_blob,
    three_way,
    tree_map,
)

PUBLISHED_CLASSES = ("identical", "stale", "contained")
UNPUBLISHED_CLASSES = ("new", "differs_clean", "differs_binary")
DECISION_CLASSES = ("differs_conflict",)


def judge(top, ref, row, wblob, oblob, base_blob):
    """Set row["class"] (and merged/reason) for one file that exists in the working tree."""
    full = os.path.join(os.fsencode(top), row["path"])
    if oblob and wblob == oblob:
        row["class"] = "identical"
    elif oblob is None:
        row["class"] = "new"
        row["merged"] = show_blob(top, wblob)
    elif wblob in published_versions(top, ref, row["path"]):
        row["class"] = "stale"
    else:
        working, theirs = show_blob(top, wblob), show_blob(top, oblob)
        if not (is_text(working) and is_text(theirs)):
            if base_blob == oblob:
                row["class"] = "differs_binary"
                row["merged"] = working
            else:
                row["class"] = "differs_conflict"
                row["reason"] = "binary changed on both sides"
            return
        theirs_lines = set(theirs.decode("utf-8").splitlines())
        unique = [ln for ln in working.decode("utf-8").splitlines() if ln.strip() and ln not in theirs_lines]
        if not unique:
            row["class"] = "contained"
            return
        merged, clean = three_way(show_blob(top, base_blob) if base_blob else b"", working, theirs)
        if clean and merged == theirs:
            row["class"] = "contained"
            row["reason"] = "merge equals the remote"
        else:
            row["class"] = "differs_clean" if clean else "differs_conflict"
            row["merged"] = merged if clean else None
            row["reason"] = f"{len(unique)} unique line(s)"


def working_rows(top, found):
    """Row per (state, path); also returns the rows that are plain files and still need judging."""
    rows, todo = [], []
    for state, path in found:
        full = os.path.join(os.fsencode(top), path)
        row = {"path": path, "state": state, "age_min": None, "class": None, "merged": None,
               "reason": "", "untracked": state[:1] == "?", "files": None}
        rows.append(row)
        if state.strip() == "D" or state[1:] == "D" or not os.path.lexists(full):
            row["class"] = "deleted"
        elif row["untracked"] and path.endswith(b"/") and os.path.isdir(full):
            # git status -unormal: one row for the whole untracked directory, never hashed
            row["class"] = "untracked_dir"
            row["files"] = count_files(full)
            row["reason"] = f"{row['files']} file(s)"
        elif not os.path.isfile(full) or os.path.islink(full) or b"\n" in path:
            row["class"] = "skipped"
            row["reason"] = "not a regular file"
        else:
            row["age_min"] = int((time.time() - os.stat(full).st_mtime) / 60)
            todo.append(row)
    return rows, todo


def classify(repo, ref, pathspecs=(), untracked="normal"):
    """(checkout root, rows) for the dirty paths, optionally limited by pathspecs.

    `untracked` is passed to git status: "normal" (one row per untracked directory), "all"
    (every file) or "no" (none).
    """
    top = out(repo, "rev-parse", "--show-toplevel").decode().strip()
    rows, todo = working_rows(top, dirty_paths(top, pathspecs, untracked))
    wblobs = hash_files(top, [r["path"] for r in todo])
    remote, head = tree_map(top, ref, pathspecs), tree_map(top, "HEAD", pathspecs)
    for row, wblob in zip(todo, wblobs):
        judge(top, ref, row, wblob, remote.get(row["path"]), head.get(row["path"]))
    return top, rows


def classify_ahead(repo, ref, pathspecs=()):
    """Rows for the files that local-only commits touched, judged by the current bytes against ref.

    A dirty-path scan cannot see a committed file whose working copy is clean. The base of the
    three-way merge is the merge-base blob, a path the remote deleted is never brought back, and
    a version the remote once held counts as `stale`.
    """
    top = out(repo, "rev-parse", "--show-toplevel").decode().strip()
    base_rev = merge_base(top, "HEAD", ref)
    paths = set()
    for line in out(top, "cherry", ref, "HEAD").decode().splitlines():
        if line.startswith("+"):
            raw = out(top, "diff-tree", "-r", "--no-commit-id", "--name-only", "-z", "--no-renames", line.split()[1])
            paths.update(p for p in raw.split(b"\0") if p)
    # git cherry omits merges; inspect each local merge against every parent.
    for commit in out(top, "rev-list", "--merges", f"{ref}..HEAD").decode().splitlines():
        raw = out(top, "diff-tree", "-m", "-r", "--no-commit-id", "--name-only", "-z", "--no-renames", commit)
        paths.update(p for p in raw.split(b"\0") if p)
    if pathspecs:
        roots = [s.encode("utf-8", "surrogateescape").rstrip(b"/") for s in pathspecs if s != "."]
        if not roots:
            roots = [b""]
        paths = {p for p in paths if any(not r or p == r or p.startswith(r + b"/") for r in roots)}
    rows, todo = working_rows(top, [("A", p) for p in sorted(paths)])
    wblobs = hash_files(top, [r["path"] for r in todo])
    remote, base = tree_map(top, ref, pathspecs), tree_map(top, base_rev, pathspecs)
    for row, wblob in zip(todo, wblobs):
        path, oblob, bblob = row["path"], remote.get(row["path"]), base.get(row["path"])
        if oblob is None and bblob is not None:
            # the remote deleted it: never bring it back; an edit made here needs a decision
            row["class"] = "skipped" if wblob == bblob else "differs_conflict"
            row["reason"] = "deleted on the remote" if wblob == bblob else "edited here, deleted on the remote"
        elif oblob is None and wblob in published_versions(top, ref, path):
            row["class"] = "stale"  # published once, deleted since
        else:
            judge(top, ref, row, wblob, oblob, bblob)
    return top, rows


def summarize(rows):
    """{class: count}."""
    counts = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    return counts


def counts_by_bucket(rows):
    """(published, unpublished, needs a decision) counts over a row list."""
    counts = summarize(rows)
    return (
        sum(counts.get(c, 0) for c in PUBLISHED_CLASSES),
        sum(counts.get(c, 0) for c in UNPUBLISHED_CLASSES),
        sum(counts.get(c, 0) for c in DECISION_CLASSES),
    )
