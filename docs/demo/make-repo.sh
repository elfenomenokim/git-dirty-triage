#!/usr/bin/env bash
# Build a throwaway repository pair for the README example.
#
# One clone publishes six commits. One clone lags and edits the same files, so its checkout holds
# every class the tool reports. Needs git only; writes under /tmp (or the path you pass) and
# refuses an existing target directory.
set -euo pipefail

root="${1:?Pass a new, nonexistent directory under /tmp}"
[ ! -e "$root" ] || { echo "Target already exists: $root" >&2; exit 1; }
mkdir -p "$root"
cd "$root"

git init -q --bare --initial-branch=main remote.git

git init -q --initial-branch=main seed
cd seed
git config user.name Seed
git config user.email seed@example.com
git remote add origin ../remote.git
printf 'a\nb\nc\n' > identical.txt
printf 'one\ntwo\n' > stale.txt
printf 'a\nb\nc\n' > contained.txt
printf 'x\ny\nz\n' > merge.txt
printf 'p\nq\nr\n' > conflict.txt
git add .
git commit -qm base
git push -q -u origin main
cd ..

# The lagging checkout exists from the start, so it never receives the peer's commits.
git clone -q remote.git shared

git clone -q remote.git peer
cd peer
git config user.name Peer
git config user.email peer@example.com
printf 'a\nb\nc\nd\n' > identical.txt
git commit -qam 'identical v2'
printf 'one\ntwo\nthree\n' > stale.txt
git commit -qam 'stale v2'
printf 'one\ntwo\nthree\nfour\n' > stale.txt
git commit -qam 'stale v3'
printf 'a\nb\nc\nd\n' > contained.txt
git commit -qam 'contained v2'
printf 'x\ny\nz\npeer-line\n' > merge.txt
git commit -qam 'merge peer'
printf 'p\npeer-q\nr\n' > conflict.txt
git commit -qam 'conflict peer'
printf 'guide v1\n' > peer-guide.md
git add peer-guide.md
git commit -qm 'peer guide'
git push -q origin main
cd ..

cd shared
git config user.name Local
git config user.email local@example.com
printf 'a\nb\nc\nd\n' > identical.txt       # equals the remote file
printf 'one\ntwo\nthree\n' > stale.txt      # an earlier published version
printf 'a\nc\nb\nd\n' > contained.txt       # only lines the remote already has
printf 'local-top\nx\ny\nz\n' > merge.txt   # one unique line, clean merge
printf 'p\nlocal-q\nr\n' > conflict.txt     # one unique line, conflicts
printf 'brand new\n' > new.txt              # not on the remote
printf 'guide v1\n' > peer-guide.md           # untracked, same bytes as the remote copy
mkdir -p build/cache                        # an untracked output tree
printf 'log line\n' > build/a.log
printf 'cache\n' > build/cache/b.log
printf 'cache\n' > build/cache/c.log

echo "demo repo: $root/shared"
