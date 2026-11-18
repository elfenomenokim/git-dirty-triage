"""Build one commit from the unpublished paths on top of the remote tip.

The commit is created on a temporary index (GIT_INDEX_FILE) from the remote tip's tree, so the
checkout's index, HEAD and working tree are not touched. Nothing is pushed.
"""

from __future__ import annotations

import os
import tempfile

from .classify import UNPUBLISHED_CLASSES
from .gitio import git, out, under

LOCAL_REF_PREFIX = "refs/git-dirty-triage/"


def unpublished_rows(rows, prefixes=()):
    """Rows a commit should carry: new, cleanly merged edits and whole-file binary replacements."""
    picked = [r for r in rows if r["class"] in UNPUBLISHED_CLASSES]
    if prefixes:
        picked = [r for r in picked if any(under(r["path"], p) for p in prefixes)]
    return sorted(picked, key=lambda r: r["path"])


def build_commit(top, parent, rows, message):
    """(commit, tree, files) for `rows` on top of `parent`; each row carries merged bytes or None."""
    parent = out(top, "rev-parse", "--verify", parent + "^{commit}").decode().strip()
    with tempfile.TemporaryDirectory(prefix="git-dirty-triage-") as d:
        env = {"GIT_INDEX_FILE": os.path.join(d, "index")}
        out(top, "read-tree", parent, env=env)
        entries = bytearray()
        for r in rows:
            full = os.path.join(os.fsencode(top), r["path"])
            data = r["merged"]
            if data is None:  # a new file: read the working bytes for this commit only
                with open(full, "rb") as fh:
                    data = fh.read()
            blob = out(top, "hash-object", "-w", "--stdin", inp=data).decode().strip()
            mode = b"100755" if os.access(full, os.X_OK) else b"100644"
            entries += mode + b" " + blob.encode() + b"\t" + r["path"] + b"\0"
        out(top, "update-index", "-z", "--add", "--index-info", inp=bytes(entries), env=env)
        tree = out(top, "write-tree", env=env).decode().strip()
    r = git(top, "commit-tree", tree, "-p", parent, "-m", message)
    if r.returncode:
        raise RuntimeError(
            "git commit-tree failed: " + r.stderr.decode("utf-8", "replace").strip()[:300]
            + " (set user.name and user.email in this repository)"
        )
    return r.stdout.decode().strip(), tree, len(rows)


def commit_unpublished(top, ref, rows, message, prefixes=(), remote="origin"):
    """Commit the unpublished clean paths on top of `ref` and point a private ref at the commit.

    Returns a JSON-ready receipt. The commit is not pushed and no branch is moved.
    """
    picked = unpublished_rows(rows, prefixes)
    branch = ref.split("/", 1)[1]
    if not picked:
        return {"status": "nothing_to_commit", "ref": ref, "files": 0}
    commit, tree, files = build_commit(top, ref, picked, message)
    local_ref = LOCAL_REF_PREFIX + branch
    out(top, "update-ref", local_ref, commit)
    return {
        "status": "committed",
        "commit": commit,
        "tree": tree,
        "parent": out(top, "rev-parse", ref + "^{commit}").decode().strip(),
        "ref": local_ref,
        "files": files,
        "paths": [r["path"].decode("utf-8", "surrogateescape") for r in picked],
        "pushed": False,
        "push": f"git push {remote} {commit}:refs/heads/{branch}",
    }
