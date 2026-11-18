"""Terminal and JSON reports."""

from __future__ import annotations

from .classify import PUBLISHED_CLASSES, counts_by_bucket, summarize
from .gitio import short_path

LABELS = [
    ("identical", "same bytes as the remote"),
    ("stale", "an earlier published version of the remote file"),
    ("contained", "the remote already holds every line"),
    ("new", "not on the remote"),
    ("differs_clean", "unpublished edit, merges cleanly"),
    ("differs_conflict", "needs a decision, conflicting lines"),
    ("differs_binary", "unpublished binary change"),
    ("deleted", "deleted in the working tree"),
    ("untracked_dir", "untracked directory, not expanded"),
    ("skipped", "skipped"),
]

NOT_PUBLISHED = (
    "new",
    "differs_clean",
    "differs_conflict",
    "differs_binary",
    "deleted",
    "untracked_dir",
    "skipped",
)


def _decision_word(count):
    return "needs" if count == 1 else "need"


def summary_line(rows, ahead=False):
    """One line: tracked changes in full detail, untracked entries as a count, separated by '·'."""
    if ahead:
        published, unpublished, decide = counts_by_bucket(rows)
        subject = f"{len(rows)} path{'' if len(rows) == 1 else 's'} touched by local-only commits"
        line = (
            f"{subject}: {published} already published, {unpublished} unpublished, "
            f"{decide} {_decision_word(decide)} a decision"
        )
        counts = summarize(rows)
        if counts.get("deleted"):
            line += f", {counts['deleted']} deleted"
        if counts.get("skipped"):
            line += f", {counts['skipped']} skipped"
        return line
    if not rows:
        return "0 dirty paths"
    tracked = [r for r in rows if not r["untracked"]]
    untracked = [r for r in rows if r["untracked"]]
    parts = []
    if tracked:
        published, unpublished, decide = counts_by_bucket(tracked)
        part = (
            f"{len(tracked)} changed tracked file{'' if len(tracked) == 1 else 's'}: "
            f"{published} already published, {unpublished} unpublished, "
            f"{decide} {_decision_word(decide)} a decision"
        )
        counts = summarize(tracked)
        if counts.get("deleted"):
            part += f", {counts['deleted']} deleted"
        if counts.get("skipped"):
            part += f", {counts['skipped']} skipped"
        parts.append(part)
    if untracked:
        part = f"{len(untracked)} untracked entr{'y' if len(untracked) == 1 else 'ies'}"
        already = sum(1 for r in untracked if r["class"] in PUBLISHED_CLASSES)
        if already:
            part += f" ({already} already on the remote)"
        parts.append(part)
    return " · ".join(parts)


def format_report(rows, behind, ref, ahead=False):
    lines = [f"checkout is {behind} commit{'' if behind == 1 else 's'} behind {ref}", summary_line(rows, ahead)]
    counts = summarize(rows)
    for key, label in LABELS:
        if counts.get(key):
            lines.append(f"  {counts[key]:>5}  {key:<17} {label}")
    for r in rows:
        if r["class"] in NOT_PUBLISHED:
            age = f"{r['age_min']:>4} min ago" if r["age_min"] is not None else " " * 11
            reason = f"  {r['reason']}" if r["reason"] else ""
            lines.append(f"        {r['class']:<17} {age}  {short_path(r['path'])}{reason}")
    return "\n".join(lines)


def json_report(rows, behind, ref, ahead=False, repo=None):
    counts = summarize(rows)
    tracked = [r for r in rows if not r["untracked"]]
    untracked = [r for r in rows if r["untracked"]]
    published, unpublished, decide = counts_by_bucket(tracked)
    tracked_counts = summarize(tracked)
    return {
        "repo": repo,
        "ref": ref,
        "behind": behind,
        "mode": "ahead" if ahead else "worktree",
        "counts": counts,
        "summary": {
            "paths": len(rows),
            "tracked": {
                "paths": len(tracked),
                "published": published,
                "unpublished": unpublished,
                "decide": decide,
                "deleted": tracked_counts.get("deleted", 0),
                "skipped": tracked_counts.get("skipped", 0),
            },
            "untracked": {
                "entries": len(untracked),
                "published": sum(1 for r in untracked if r["class"] in PUBLISHED_CLASSES),
            },
        },
        "paths": [
            {
                "path": r["path"].decode("utf-8", "surrogateescape"),
                "class": r["class"],
                "age_min": r["age_min"],
                "reason": r["reason"],
                "untracked": r["untracked"],
                "files": r["files"],
            }
            for r in rows
        ],
    }
