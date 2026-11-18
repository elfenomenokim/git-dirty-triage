export PS1='$ '
export PYTHONPATH="$PWD/src"
git-dirty-triage() { python3 -m git_dirty_triage "$@"; }
demo_root="$(mktemp -d /tmp/git-triage-demo.XXXXXX)"
bash docs/demo/make-repo.sh "$demo_root/repo" >/dev/null 2>&1
cd "$demo_root/repo/shared"
clear
