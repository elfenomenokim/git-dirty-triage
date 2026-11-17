# git-dirty-triage

[English](https://github.com/elfenomenokim/git-dirty-triage/blob/main/README.md)

뒤처진 체크아웃에서 수정된 파일 가운데 무엇이 진짜 아직 게시되지 않은 것인지 가려냅니다.

```console
$ git-dirty-triage
checkout is 7 commits behind origin/main
5 changed tracked files: 3 already published, 1 unpublished, 1 needs a decision · 3 untracked entries (1 already on the remote)
      2  identical         same bytes as the remote
      1  stale             an earlier published version of the remote file
      1  contained         the remote already holds every line
      1  new               not on the remote
      1  differs_clean     unpublished edit, merges cleanly
      1  differs_conflict  needs a decision, conflicting lines
      1  untracked_dir     untracked directory, not expanded
        differs_conflict     0 min ago  conflict.txt  1 unique line(s)
        differs_clean        0 min ago  merge.txt  1 unique line(s)
        untracked_dir                  build/  3 file(s)
        new                  0 min ago  new.txt
```

## 왜 쓰나

여러 에이전트나 세션이 체크아웃 하나를 같이 씁니다. 한쪽이 작업을 게시하면 원격 끝 위에 커밋을 만들어 푸시합니다. 그 순간 다른 세션이 같은 파일을 고치고 있어서, 공유 체크아웃의 브랜치는 앞으로 당기지 않습니다. 브랜치는 일부러 뒤처지고, `git status`는 이미 원격에 있는 작업까지 계속 수정된 것으로 보여 줍니다.

그 목록을 그대로 믿으면 손해가 납니다. 나중에 "전부 커밋해서 푸시"하면 낡은 로컬 HEAD 위에 커밋이 만들어지고, 원격의 더 새로운 같은 파일과 부딪힙니다. 충돌은 어느 쪽 편집에도 없습니다. 게시하는 쪽에서 생깁니다.

`git status`는 수정된 파일 중 무엇에 새 내용이 있는지 알려 주지 못합니다. 작업 트리를 로컬 인덱스와 비교할 뿐, 원격과 비교하지 않습니다. 이 도구는 수정된 경로마다 원격 끝과 바이트를 비교해서 실제 질문에 답합니다.

- 원격 파일과 바이트가 같습니다. 이미 게시됐고, 할 일이 없습니다.
- 예전에 게시된 버전과 같습니다. 이것도 게시된 것입니다.
- 모든 줄이 원격 파일에 이미 있습니다. 새 내용이 없습니다.
- 원격에 없는 바이트입니다. 아직 게시되지 않았습니다.

추적하지 않는 디렉터리는 이 목록을 더 나쁘게 만듭니다. 빌드 출력 디렉터리는 아무도 고치지 않은 파일 수천 개이고, 그걸 전부 펼치면 진짜 변경 몇 개가 묻힙니다. 기본값에서 git은 추적하지 않는 디렉터리를 `build/` 한 줄로 보여 주고, 이 도구도 그대로 둡니다. 한 줄, 해시 없음, 커밋 없음입니다. 추적하지 않는 파일 자체는 여전히 분류하므로, 원격에 이미 있는 파일은 게시된 것으로 셉니다.

`--commit-unpublished` 없이 실행하면 읽기만 합니다. 커밋 옵션은 커밋 객체와 전용 ref를 만들지만, 브랜치도 인덱스도 작업 트리도 움직이지 않습니다.

## 설치

```console
$ pipx install git-dirty-triage     # 권장: 격리 설치, PATH에 명령이 생깁니다
$ uvx git-dirty-triage --help       # 설치 없이 한 번만 실행
$ pip install git-dirty-triage      # 프로젝트 안에서
```

Python 3.9 이상, git 2.x가 필요합니다. 파이썬 의존성은 없습니다. 설치되는 명령 이름이 `git-dirty-triage`라서 git이 `git dirty-triage`로도 실행합니다.

## 쓰는 법

### 수정된 경로 분류하기

```console
$ git-dirty-triage
```

먼저 해당 브랜치를 가져온 뒤 비교합니다. 첫 줄은 체크아웃이 얼마나 뒤처졌는지, 둘째 줄은 판단에 필요한 개수입니다. `·`로 나뉜 두 부분입니다. 앞은 추적 중인 변경을 자세히, 뒤는 추적하지 않는 항목을 개수로 보여 줍니다. 그 아래에는 이미 게시된 것을 뺀 경로만 나열합니다. 순서는 `git status` 순서이고, 긴 경로는 왼쪽을 줄여서 보여 줍니다.

요약 아래 분류별 개수는 추적하지 않는 파일까지 포함한 모든 행을 셉니다. 요약 줄은 추적 변경과 추적하지 않는 항목을 나눠서, 추적하지 않는 파일이 원격에 이미 있으면 두 숫자가 다릅니다.

### 추적하지 않는 경로

`-u/--untracked`는 git status와 같은 뜻입니다.

| 값 | 추적하지 않는 디렉터리 | 추적하지 않는 파일 |
|---|---|---|
| `normal` (기본) | `build/` 한 줄, 파일 개수 포함 | 각자 한 줄, 분류함 |
| `all` | 펼침: 파일마다 한 줄, 분류함 | 각자 한 줄, 분류함 |
| `no` | 표시 안 함 | 표시 안 함 |

```console
$ git-dirty-triage --prefix build
checkout is 7 commits behind origin/main
1 untracked entry
      1  untracked_dir     untracked directory, not expanded
        untracked_dir                  build/  3 file(s)

$ git-dirty-triage --prefix build --untracked all
checkout is 7 commits behind origin/main
3 untracked entries
      3  new               not on the remote
        new                  0 min ago  build/a.log
        new                  0 min ago  build/cache/b.log
        new                  0 min ago  build/cache/c.log
```

파일 개수는 디렉터리를 한 번 훑어서 셉니다. 추적하지 않는 디렉터리 안의 파일은 해시하지도, 원격과 비교하지도 않습니다. `untracked_dir` 행은 `--print-unpublished`가 출력하지 않고 커밋하지도 않습니다. 그 안의 파일이 필요하면 `--untracked all`을 씁니다.

### 아직 게시되지 않은 경로만 출력하기

```console
$ git-dirty-triage --print-unpublished
merge.txt
new.txt
```

한 줄에 경로 하나입니다. 그대로 파이프로 넘길 수 있습니다. 추적하지 않는 디렉터리는 출력하지 않고, 추적하지 않는 파일은 출력합니다. 파일 이름에 줄바꿈이 있는 경로는 `skipped`로 보고하고 출력하지 않으므로, 한 줄은 언제나 경로 하나입니다.

```console
$ git-dirty-triage --print-unpublished | while IFS= read -r p; do git add -- "$p"; done
```

### 원격 끝 위에 커밋하고, 푸시는 하지 않기

```console
$ git-dirty-triage --commit-unpublished -m "local work"
committed 2 path(s) as 08627b9a8f3ccfca858b1c32dd5bc5ac2135915e on top of origin/main
  ref:  refs/git-dirty-triage/main
  push: not pushed
  next: git push origin 08627b9a8f3ccfca858b1c32dd5bc5ac2135915e:refs/heads/main
```

커밋은 원격 끝의 트리로 임시 인덱스에서 만듭니다. 부모는 `origin/main`이고, 로컬 HEAD가 아닙니다. 고친 텍스트는 내 바이트와 원격 바이트를 3방향 병합한 결과를 넣습니다. 어느 쪽 줄도 잃지 않습니다. 새 파일과 바이너리는 통째로 넣습니다. 브랜치, 인덱스, 작업 트리는 그대로 두고, 푸시도 하지 않습니다.

커밋은 `refs/git-dirty-triage/<브랜치>`로 남습니다. 확인한 뒤에 푸시합니다. 원격에 그 바이트가 실제로 생기기 전까지는 다시 실행해도 그 경로를 아직 게시되지 않은 것으로 보고합니다. 이 도구가 답하는 질문이 그것입니다.

충돌하는 경로는 커밋하지 않습니다. 그 경로를 고치는 세션이 풉니다. 체인지로그나 원장을 줄 단위 합집합으로 합치는 것은 해결이 아닙니다.

### 로컬 커밋만 건드린 파일

`--ahead`는 나머지 사각지대를 봅니다. 로컬에서 커밋했지만 원격에는 닿지 않았고, 작업 사본은 깨끗한 파일입니다. 수정 경로만 훑는 검사는 이 파일을 못 봅니다.

```console
$ git-dirty-triage --ahead
checkout is 7 commits behind origin/main
1 path touched by local-only commits: 0 already published, 1 unpublished, 0 need a decision
      1  new               not on the remote
        new                  0 min ago  notes.txt
```

3방향 병합의 기준은 `HEAD`가 아니라 merge-base 블롭입니다. 원격이 지운 경로는 되살리지 않고, 원격이 예전에 가졌던 버전은 `stale`로 봅니다. `--ahead`는 커밋 내용을 읽으므로 `--untracked`가 적용되지 않습니다.

### 디렉터리나 파일 하나만

```console
$ git-dirty-triage --prefix src --prefix README.md
```

`--prefix`는 보고서뿐 아니라 목록 자체를 좁힙니다. 그래서 작업 단위 하나는 자기 경로만큼만 비용이 듭니다. 접두사는 저장소 기준 상대 경로입니다.

### 기계가 읽을 출력

```console
$ git-dirty-triage --json
{"repo": "/tmp/demo/shared", "ref": "origin/main", "behind": 7, "mode": "worktree",
 "counts": {"identical": 2, "stale": 1, "contained": 1, "new": 1, "differs_clean": 1,
            "differs_conflict": 1, "untracked_dir": 1},
 "summary": {"paths": 8,
             "tracked": {"paths": 5, "published": 3, "unpublished": 1, "decide": 1, "deleted": 0, "skipped": 0},
             "untracked": {"entries": 3, "published": 1}},
 "paths": [{"path": "conflict.txt", "class": "differs_conflict", "age_min": 0,
            "reason": "1 unique line(s)", "untracked": false, "files": null}, …]}
```

(읽기 쉽도록 줄을 나누고 줄인 것입니다. 실제로는 한 줄로 나옵니다.)

모든 행에 `untracked`와 `files`가 있습니다. `files`는 `untracked_dir` 행의 파일 개수이고, 나머지는 `null`입니다.

`--commit-unpublished --json`은 영수증을 출력합니다. `status`, `commit`, `parent`, `ref`, `files`, `paths`, `pushed`, `push` 명령이 들어 있고, 커밋할 것이 없으면 `{"status": "nothing_to_commit"}`입니다.

### 종료 코드

`0`은 보고서를 출력했다는 뜻입니다. 아직 게시되지 않은 경로나 충돌을 보고해도 `0`입니다. 보고서는 데이터입니다. `2`는 사용법이나 git 오류입니다. `--commit-unpublished`에서는 `nothing to commit`도 `0`입니다.

## 판정 기준

| 분류 | 원격 끝과 비교한 작업 바이트 | 게시 여부 |
|---|---|---|
| `identical` | 원격과 같은 블롭 | 게시됨 |
| `stale` | 그 경로가 예전에 가졌던 게시 버전과 같음 | 게시됨 |
| `contained` | 비어 있지 않은 모든 줄이 원격 파일에 이미 있음 | 게시됨 |
| `new` | 원격에 이 경로의 파일이 없음 | 미게시 |
| `differs_clean` | 새 줄이 있고, `HEAD`를 기준으로 한 3방향 병합이 깨끗함 | 미게시 |
| `differs_conflict` | 새 줄이 있고, 같은 병합이 충돌함 | 판단 필요 |
| `differs_binary` | 바이너리이고, `HEAD` 이후 원격 블롭이 바뀌지 않음 | 미게시, 통째로 |
| `deleted` | 작업 트리에서 지워짐 | 보고만 |
| `untracked_dir` | `--untracked normal`에서 추적하지 않는 디렉터리 | 한 줄, 해시·출력·커밋 없음 |
| `skipped` | 일반 파일이 아님(심볼릭 링크, 줄바꿈이 든 경로) | 보고만 |

깨끗하게 병합한 결과가 원격 바이트와 같으면 `contained`입니다. 그 경로는 뒤처져 있을 뿐입니다.

비용은 묶음 `hash-object` 한 번과 양쪽 `ls-tree` 한 번입니다. 경로별 이력은 정말 다른 경로에만 읽습니다. 경로 38,925개짜리 체크아웃을 Apple 실리콘 Mac(Python 3.12, 캐시가 더워진 상태)에서 107초에 분류했습니다.

## 실제 예시

이 문서 맨 위의 출력은 `examples/make-demo.sh`에서 나옵니다. 임시 디렉터리에 원격 하나와 클론 둘을 만듭니다. `peer`가 커밋 일곱 개를 게시하고, `shared`는 뒤처진 채로 같은 파일 다섯 개와 새 파일 하나, 게시된 파일의 추적하지 않는 사본 하나, 추적하지 않는 `build/` 트리를 만듭니다.

```console
$ bash examples/make-demo.sh
demo repo: /tmp/git-dirty-triage-demo/shared
$ cd /tmp/git-dirty-triage-demo/shared && git-dirty-triage
```

## 이런 때는 필요 없습니다

- **에이전트마다 클론이나 워크트리를 따로 씁니다.** 각 체크아웃이 원격을 따라가므로 `git status`가 이미 사실입니다.
- **체크아웃이 원격과 같은 지점에 있습니다.** 같은 이유입니다.
- **작성자가 하나이고 동시에 게시하는 쪽이 없습니다.** 뒤에서 게시될 일이 없습니다.
- **두 브랜치가 병합될지 알고 싶습니다.** `git merge-tree`나 `git range-diff`를 씁니다. 이 도구는 작업 트리 하나를 원격 브랜치 하나와 비교합니다.

체크아웃이 일부러 뒤처져 있는데 수정도 남아 있는 상태, 여러 에이전트가 체크아웃 하나를 쓰면 생기는 그 상태에서 필요합니다.

## 한계

- **답은 마지막 fetch를 기준으로 합니다.** 기본으로 가져오고, fetch가 실패하면 경고를 출력한 뒤 이미 가져온 것으로 비교합니다. `--no-fetch`은 가져오지 않고 조용히 넘어갑니다.
- **파일만 봅니다.** 디렉터리는 분류하지 않고, 이름 변경은 삭제와 새 파일로 나옵니다. 삭제와 건너뛴 경로는 보고만 하고 커밋하지 않습니다.
- **"미게시"가 "필요함"은 아닙니다.** 깨끗하게 병합되는 편집은 정의상 미게시입니다. 커밋에 넣을지는 직접 정합니다.
- **바이너리는 전부 아니면 전무**이고, `HEAD` 이후 원격 사본이 바뀌지 않았을 때만 됩니다. 그 밖에는 판단이 필요합니다.
- **커밋된 편집은 작업 파일과 다를 수 있습니다.** `differs_clean`의 커밋에는 3방향 병합 결과가 들어가고, 디스크의 바이트와 다를 수 있습니다. 작업 트리는 그대로 둡니다.
- **추적하지 않는 디렉터리는 기본값에서 불투명합니다.** 파일 개수는 디렉터리를 한 번 훑어서 세고, 안의 파일은 해시하거나 원격과 비교하지 않습니다. `--untracked all`은 그 디렉터리를 펼치는데, 큰 빌드 트리에서는 비싸고, 그 안의 파일을 보고·출력·커밋하는 유일한 방법입니다.
- **`--ahead`는 merge-base가 필요합니다.** 깊이 1의 얕은 클론에는 없습니다.
- **빈 저장소는 지원하지 않습니다.** 비교할 원격 끝이 없습니다.
- **macOS(Apple 실리콘, Python 3.12)에서 시험했습니다.** 표준 라이브러리와 `git`만 쓰지만 Linux와 Windows는 시험하지 않았습니다. 써 보고 알려 주시면 반영하겠습니다.
- **수정된 경로가 아주 많으면** 정말 다른 파일마다 `cat-file`과 `log`를 한 번씩 부릅니다. 같은 파일과 새 파일만 있으면 쌉니다.

설정 파일도 환경변수도 없습니다. 기본값은 모두 플래그로 바꿉니다. `--repo`, `--remote`, `--branch`, `--untracked`입니다.

## 에이전트에서 쓰기

AI 에이전트가 공유 체크아웃에서 작업을 게시해야 한다면 [AGENTS.md](https://github.com/elfenomenokim/git-dirty-triage/blob/main/AGENTS.md)를 읽으세요. Claude Code 스킬은 [`skill/git-dirty-triage/SKILL.md`](https://github.com/elfenomenokim/git-dirty-triage/blob/main/skill/git-dirty-triage/SKILL.md)에 있습니다. 이 폴더를 `~/.claude/skills/git-dirty-triage/`로 복사하면 설치됩니다.

## 라이선스

MIT입니다. [LICENSE](https://github.com/elfenomenokim/git-dirty-triage/blob/main/LICENSE)를 보세요.
