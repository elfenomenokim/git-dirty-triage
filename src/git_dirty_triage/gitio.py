"""Thin wrappers over the git plumbing this tool needs.

Every call here is read-only. The committer builds its objects with the same wrappers, on a
temporary index, so the checkout's own index and HEAD are never touched.
"""

from __future__ import annotations

import os
import subprocess
import tempfile


def git(repo, *args, inp=None, env=None, check=False):
    """Run git inside `repo` with literal pathspecs; return the CompletedProcess."""
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run(
        ["git", "-C", repo, "--literal-pathspecs", *args],
        capture_output=True,
        input=inp,
        env=e,
    )
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args[:3])} failed: {r.stderr.decode('utf-8', 'replace')[:300]}")
    return r


def out(repo, *args, inp=None, env=None):
    return git(repo, *args, inp=inp, env=env, check=True).stdout


def toplevel(repo):
    """Absolute path of the working-tree root; raises with a readable message outside a checkout."""
    r = git(repo, "rev-parse", "--show-toplevel")
    if r.returncode:
        raise RuntimeError(f"{repo} is not a git checkout: {r.stderr.decode('utf-8', 'replace').strip()[:200]}")
    return r.stdout.decode().strip()


def dirty_paths(repo, pathspecs=(), untracked="normal"):
    """[(two-letter status, path bytes)] under `pathspecs`.

    `untracked` follows git status: "normal" lists an untracked directory as one trailing-slash
    entry, "all" lists every file inside it, "no" skips untracked paths.
    """
    cmd = ["status", "--porcelain=v1", "-z", f"--untracked-files={untracked}"]
    if pathspecs:
        cmd += ["--", *pathspecs]
    records = out(repo, *cmd).split(b"\0")
    found, i = [], 0
    while i < len(records):
        rec = records[i]
        if rec:
            state, path = rec[:2].decode(), rec[3:]
            found.append((state, path))
            if state[:1] in "RC":
                i += 1  # a rename or copy record carries the source path in the next field
        i += 1
    return found


def tree_map(repo, rev, pathspecs=()):
    """{path bytes: blob id} for every file at `rev`, optionally under `pathspecs`."""
    cmd = ["ls-tree", "-r", "-z", rev]
    if pathspecs:
        cmd += ["--", *pathspecs]
    blobs = {}
    for rec in out(repo, *cmd).split(b"\0"):
        if rec:
            meta, path = rec.split(b"\t", 1)
            blobs[path] = meta.split()[2].decode()
    return blobs


def hash_files(repo, paths):
    """Blob id of each working file, in order: one hash-object call per 5,000 paths."""
    if not paths:
        return []
    ids = []
    for i in range(0, len(paths), 5000):
        chunk = paths[i:i + 5000]
        ids += out(repo, "hash-object", "--stdin-paths", inp=b"\n".join(chunk) + b"\n").decode().split()
    return ids


def show_blob(repo, blob):
    return out(repo, "cat-file", "blob", blob)


def published_versions(repo, ref, path, limit=300):
    """Blob ids this path has had on `ref` (most recent `limit` commits that touched it)."""
    p = path.decode("utf-8", "surrogateescape")
    commits = out(repo, "log", f"-n{limit}", "--format=%H", ref, "--", p).decode().split()
    if not commits:
        return set()
    query = "".join(f"{c}:{p}\n" for c in commits).encode("utf-8", "surrogateescape")
    res = out(repo, "cat-file", "--batch-check", inp=query).decode("utf-8", "replace").splitlines()
    return {line.split()[0] for line in res if len(line.split()) >= 3 and line.split()[1] == "blob"}


def merge_base(repo, a, b):
    return out(repo, "merge-base", a, b).decode().strip()


def is_text(data):
    if b"\0" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def three_way(base, ours, theirs):
    """(merged bytes, clean?) through git merge-file with a temporary directory."""
    with tempfile.TemporaryDirectory(prefix="git-dirty-triage-") as d:
        paths = []
        for name, data in (("ours", ours), ("base", base), ("theirs", theirs)):
            p = os.path.join(d, name)
            with open(p, "wb") as fh:
                fh.write(data)
            paths.append(p)
        r = subprocess.run(["git", "merge-file", "-p", *paths], capture_output=True)
        return r.stdout, r.returncode == 0


def under(path, prefix):
    """True when a repo-relative path is the prefix itself or sits below it."""
    p = prefix.rstrip(b"/")
    return path == p or path.startswith(p + b"/")


def pathspecs_for(top, prefixes):
    """Pathspecs that cannot leave out a path a prefix selects.

    An existing path is used as it is; otherwise its parent directory; [] (the whole checkout)
    when a prefix has no parent directory to start from.
    """
    specs = []
    for prefix in prefixes:
        p = prefix.decode("utf-8", "surrogateescape")
        if os.path.exists(os.path.join(top, p)):
            specs.append(p.rstrip("/") or ".")
        elif os.path.dirname(p):
            specs.append(os.path.dirname(p))
        else:
            return []
    return specs


def count_files(root):
    """Number of non-directory entries under `root`; symlinks to directories are not followed."""
    total = 0
    for _dirpath, _dirnames, filenames in os.walk(root):
        total += len(filenames)
    return total


def short_path(path, n=90):
    """Path for one terminal line, shortened from the left when long and with control characters escaped."""
    s = path.decode("utf-8", "surrogateescape")
    s = s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return s if len(s) <= n else "..." + s[-(n - 3):]


def remote_branches(top, remote):
    prefix = f"refs/remotes/{remote}/"
    listing = git(top, "for-each-ref", "--format=%(refname)", prefix)
    return {
        line[len(prefix):]
        for line in listing.stdout.decode("utf-8", "replace").splitlines()
        if line.startswith(prefix) and line != prefix + "HEAD"
    }


def remote_default_branch(top, remote):
    """The branch the remote's HEAD points at, read without fetching."""
    r = git(top, "ls-remote", "--symref", remote, "HEAD")
    if r.returncode:
        return None
    for line in r.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("ref: ") and line.endswith("\tHEAD"):
            target = line[5:].split("\t")[0].strip()
            if target.startswith("refs/heads/"):
                return target[len("refs/heads/"):]
    return None


def resolve_ref(top, remote, branch):
    """remote/branch to compare with: the flag, the remote's default, main, master, or the current branch."""
    if branch:
        return f"{remote}/{branch}"
    configured = out(top, "remote").decode().split()
    if remote not in configured:
        raise RuntimeError(
            f"no remote named '{remote}' (configured: {', '.join(configured) or 'none'}); pass --remote"
        )
    names = remote_branches(top, remote)
    head = git(top, "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD")
    if head.returncode == 0:
        target = head.stdout.decode().strip()
        candidate = target[len(f"refs/remotes/{remote}/"):] if target.startswith(f"refs/remotes/{remote}/") else ""
        if candidate in names:
            return f"{remote}/{candidate}"
    for name in ("main", "master"):
        if name in names:
            return f"{remote}/{name}"
    current = git(top, "symbolic-ref", "--short", "--quiet", "HEAD")
    if current.returncode == 0 and current.stdout.decode().strip() in names:
        return f"{remote}/{current.stdout.decode().strip()}"
    default = remote_default_branch(top, remote)
    if default:
        return f"{remote}/{default}"
    known = ", ".join(sorted(names)) if names else "none fetched"
    raise RuntimeError(f"no branch found on remote '{remote}' ({known}); pass --branch")
