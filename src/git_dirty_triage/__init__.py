"""In a lagging shared checkout, tell which modified files are really unpublished.

    from git_dirty_triage import classify, summarize

    top, rows = classify("/path/to/checkout", "origin/main")
    print(summarize(rows))
"""

from .classify import (
    DECISION_CLASSES,
    PUBLISHED_CLASSES,
    UNPUBLISHED_CLASSES,
    classify,
    classify_ahead,
    counts_by_bucket,
    summarize,
)
from .commit import build_commit, commit_unpublished, unpublished_rows
from .gitio import git, is_text, out, pathspecs_for, resolve_ref, short_path, toplevel, under
from .report import format_report, json_report, summary_line

__version__ = "0.1.1"

__all__ = [
    "__version__",
    "PUBLISHED_CLASSES",
    "UNPUBLISHED_CLASSES",
    "DECISION_CLASSES",
    "classify",
    "classify_ahead",
    "summarize",
    "counts_by_bucket",
    "unpublished_rows",
    "build_commit",
    "commit_unpublished",
    "format_report",
    "json_report",
    "summary_line",
    "git",
    "out",
    "toplevel",
    "is_text",
    "resolve_ref",
    "pathspecs_for",
    "short_path",
    "under",
]
