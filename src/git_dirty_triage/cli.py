"""Command line: git-dirty-triage."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from . import __version__
from .classify import UNPUBLISHED_CLASSES, classify, classify_ahead
from .commit import commit_unpublished
from .gitio import git, out, pathspecs_for, resolve_ref, toplevel, under
from .report import format_report, json_report

DESCRIPTION = (
    "In a checkout that lags behind its remote, show which modified files are already published "
    "and which carry something new."
)


def build_parser():
    p = argparse.ArgumentParser(prog="git-dirty-triage", description=DESCRIPTION)
    p.add_argument("--repo", default=".", help="checkout to inspect (default: the current directory)")
    p.add_argument("--remote", default="origin", help="remote to compare with (default: origin)")
    p.add_argument("--branch", default=None,
                   help="remote branch (default: the remote's default branch, then main, then master)")
    p.add_argument("--prefix", action="append", default=[], metavar="PATH",
                   help="limit the listing and the report to this repo-relative path (repeatable)")
    p.add_argument("--ahead", action="store_true",
                   help="judge the files that local-only commits touched instead of the dirty paths")
    p.add_argument("-u", "--untracked", choices=("no", "normal", "all"), default="normal",
                   help="untracked paths: 'normal' lists an untracked directory as one row (default), "
                        "'all' lists every untracked file, 'no' skips them")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--print-unpublished", action="store_true",
                      help="print only the unpublished paths, one per line, for piping to git add")
    mode.add_argument("--commit-unpublished", action="store_true",
                      help="commit the unpublished clean paths on top of the remote tip; nothing is pushed")
    p.add_argument("-m", "--message", help="commit message for --commit-unpublished")
    p.add_argument("--no-fetch", action="store_true", help="compare with the last fetched remote ref")
    p.add_argument("--json", action="store_true", help="print one JSON object")
    p.add_argument("--version", action="version", version=f"git-dirty-triage {__version__}")
    return p


def main(argv=None):
    parser = build_parser()
    a = parser.parse_args(argv)
    if a.commit_unpublished and not a.message:
        parser.error("--commit-unpublished needs -m/--message")
    for prefix in a.prefix:
        if os.path.isabs(prefix) or ".." in prefix.split("/"):
            parser.error(f"--prefix must be a repo-relative path: {prefix}")
    try:
        top = toplevel(a.repo)
        ref = resolve_ref(top, a.remote, a.branch)
        branch = ref.split("/", 1)[1]
        fetched = None if a.no_fetch else git(top, "fetch", a.remote, branch)
        if git(top, "rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode:
            detail = fetched.stderr.decode("utf-8", "replace").strip()[:200] if fetched is not None else ""
            raise RuntimeError(f"{ref} does not exist; pass --branch or fetch {a.remote} first"
                               + (f" ({detail})" if detail else ""))
        if fetched is not None and fetched.returncode:
            print(f"warning: git fetch {a.remote} {branch} failed; comparing with the last fetched {ref}",
                  file=sys.stderr)
        prefixes = [os.fsencode(x) for x in a.prefix]
        specs = pathspecs_for(top, prefixes)
        rows = (classify_ahead(top, ref, specs) if a.ahead else classify(top, ref, specs, a.untracked))[1]
        if prefixes:
            rows = [r for r in rows if any(under(r["path"], x) for x in prefixes)]
        behind = int(out(top, "rev-list", "--count", f"HEAD..{ref}").decode().strip())
    except (RuntimeError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if a.print_unpublished:
        for path in sorted(r["path"] for r in rows if r["class"] in UNPUBLISHED_CLASSES):
            print(path.decode("utf-8", "surrogateescape"))
        return 0

    if a.commit_unpublished:
        try:
            receipt = commit_unpublished(top, ref, rows, a.message, prefixes, a.remote)
        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        if a.json:
            print(json.dumps(receipt, ensure_ascii=False))
            return 0
        if receipt["status"] == "nothing_to_commit":
            print("nothing to commit: no unpublished path needs a commit")
        else:
            print(f"committed {receipt['files']} path(s) as {receipt['commit']} on top of {ref}")
            print(f"  ref:  {receipt['ref']}")
            print("  push: not pushed")
            print(f"  next: {receipt['push']}")
        return 0

    if a.json:
        print(json.dumps(json_report(rows, behind, ref, a.ahead, top), ensure_ascii=False))
    else:
        print(format_report(rows, behind, ref, a.ahead))
    return 0


if __name__ == "__main__":
    sys.exit(main())
