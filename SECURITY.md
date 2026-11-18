# Security policy

## Supported versions

Security fixes go into the latest release. Upgrade before reporting, in case the problem is
already fixed.

| Version | Supported |
| --- | --- |
| 0.1.3 | Yes |
| Older | No |

## Reporting a vulnerability

Report it privately, not in a public issue: use the
[Report a vulnerability](https://github.com/elfenomenokim/git-dirty-triage/security/advisories/new)
form on the repository's Security tab.

Include the command, the version (`git-dirty-triage --version`), your Git version, and what an
attacker could do with the result. You get a reply within a few days.

## In scope

- A commit built from bytes that differ from the working tree, for example with a clean filter or
  line-ending normalisation bypassed.
- A push, a ref update or a write to the remote that the caller did not ask for.
- A path that is committed although it was classified as unpublished-unsafe, opaque or untracked
  without being expanded.
- A repository path, a filename or a Git config value that makes the tool run a command it was not
  asked to run, or read a file outside the repository.
- A filename that breaks the classification, so other dirty paths are neither reported nor
  committed.

## Not a vulnerability

- Publishing an edit because you asked for `--commit-unpublished`. The tool commits what it
  classified; read the report first.
- A cached remote ref that is stale because the fetch failed. The tool prints a warning and says
  the evidence is not fresh.
- Classifying a large checkout slowly. Unique differences need per-path history and content reads;
  use `--prefix` to narrow the work.

## Disclosure

Once a fix is released, the advisory is published with credit to the reporter unless they prefer
otherwise.
