# prompts/commands.md
# 역할: git-scoped-account의 입력 수집·탐지·적용·검증 명령과 규칙

---

## 라우팅 표

| 단계 | 읽을 섹션 |
|------|----------|
| 입력 확보 | [입력 수집] |
| 대상 repo 찾기 | [탐지] |
| 설정 적용 | [적용] |
| 적용 확인 | [검증] |
| 공통 규칙 | [경로·안전 규칙] |

---

## [입력 수집]

### 🔴 필수 (추론 불가 시에만 질문, 한 번에 최대 2개)

1. **프로젝트 최상위(컨테이너) 디렉토리 경로** — 이 폴더 자체는 git repo가 아니며, 바로 아래 애플리케이션 repo들에 적용한다. (예: `C:\dev\project-a`)
2. **git 계정** — `user.name`과 `user.email`.

### 추론 우선

- 사용자가 특정 폴더에서 작업 중이거나 메시지에 경로를 줬으면 그 경로를 후보로 제시한다.
- name/email을 한쪽만 줬으면 나머지만 묻는다.
- 공통 config 파일명은 호스트/용도에서 자동 제안한다. (예: gitea → `.gitconfig-gitea`, 기본 → `.gitconfig-scoped`)

---

## [탐지]

프로젝트 최상위(컨테이너) 디렉토리 자체는 git repo가 아니어야 하며 적용 대상에도 넣지 않는다. 바로 아래 **1단계** 폴더 중 `.git`이 있는 애플리케이션 repo만 찾는다. 재귀하지 않는다.

### PowerShell (win32 기본)

```powershell
$base = "C:\dev\project-a"

if (Test-Path (Join-Path $base ".git")) {
  Write-Output "WARN: 기준 디렉토리 자체가 git repo입니다. 이 스킬은 git으로 관리하지 않는 프로젝트 최상위 폴더 아래의 애플리케이션 repo들에 적용합니다."
}

Get-ChildItem -LiteralPath $base -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName ".git") } |
  Select-Object -ExpandProperty FullName
```

### POSIX (Bash 대안)

```bash
base="/c/dev/project-a"
[ -e "$base/.git" ] && printf '%s\n' "WARN: 기준 디렉토리 자체가 git repo입니다. 이 스킬은 git으로 관리하지 않는 프로젝트 최상위 폴더 아래의 애플리케이션 repo들에 적용합니다."
for d in "$base"/*/; do
  [ -e "$d/.git" ] && printf '%s\n' "${d%/}"
done
```

> 결과 0건이면 "프로젝트 최상위 폴더 바로 아래 1단계에 git repo가 없습니다"라고 알리고 종료한다.
> 기준 디렉토리 자체와 2단계 이상 중첩 repo에는 적용하지 않는다.
> 전체 트리 재귀 스캔으로 fallback 하지 않는다.

---

## [적용]

승인 후에만 실행한다. 전체 대상은 하나의 트랜잭션처럼 취급한다. 일부 repo만 변경된 상태로 남기지 않는다.

### 1) 전체 사전 점검과 byte 스냅샷

쓰기 전에 다음을 모두 수행한다.

- 대상 repo와 공통 config 경로를 절대경로로 확정하고, 경계 밖 경로가 없는지 확인한다.
- 각 repo의 실제 로컬 config 경로는 `git -C <repo> rev-parse --path-format=absolute --git-path config`로 구한다.
- 공통 config가 존재하는지와 기존 바이트, 각 repo 로컬 config의 기존 바이트를 작업 전용 임시 디렉토리에 복사한다.
- 공통 config가 이미 있으면 기존 내용을 먼저 보여주고 덮어쓸지 별도로 확인받는다.
- 모든 대상이 읽기·쓰기 가능한지 사전 점검한다. 하나라도 실패하면 아무것도 바꾸지 않고 종료한다.
- 스냅샷은 텍스트로 재생성하지 않고 파일 바이트를 그대로 복사한다. 권한 등 메타데이터도 가능한 범위에서 보존한다.

PowerShell에서는 `Copy-Item -LiteralPath`, POSIX에서는 `cp -p --`처럼 경로를 인자로 안전하게 전달한다. 임시 경로는 사용자 프로젝트 밖의 작업 전용 임시 디렉토리를 사용한다.

### 2) 공통 config 파일 원자적 반영

`templates/gitconfig-shared.md` 구조로 임시 파일을 먼저 만들고 구문과 값을 확인한 다음 프로젝트 최상위(컨테이너) 디렉토리의 최종 경로로 교체한다. 토큰·비밀번호나 기존 파일의 불필요한 설정을 섞지 않는다.

### 3) 각 repo의 include.path를 정확한 값으로 정규화

`include.path` 값은 **공통 config 파일의 슬래시(`/`) 절대경로**다. git config 값에서 역슬래시는 이스케이프 문자로 해석되므로 Windows 경로도 `/`로 변환한다.

각 repo에서 아래 순서를 지킨다.

1. `git -C <repo> config --local --fixed-value --get-all include.path "<configPath>"`로 **관리 대상 값과 정확히 같은 값만** 조회한다.
2. 결과가 0개면 `git -C <repo> config --local --add include.path "<configPath>"`로 추가한다.
3. 결과가 1개면 변경하지 않는다.
4. 결과가 2개 이상이면
   `git -C <repo> config --local --fixed-value --unset-all include.path "<configPath>"`로 그 값만 제거한 뒤
   `--add`로 한 번 추가한다.
5. `git -C <repo> config --local --get-all include.path` 전체 결과와 작업 전 스냅샷을 비교해, 관리 대상 외 값의 내용과 순서가 보존되었는지 확인한다.

`--unset-all include.path`처럼 값 조건이 없는 명령은 금지한다. 정규식 비교도 쓰지 않고 항상 `--fixed-value`로 대상 값을 고정한다.

이전 관리 경로에서 새 경로로 이관해야 하면 기존 경로를 명시해 사용자에게 보여주고 별도 승인을 받은 뒤, 그 **정확한 기존 값만** `--fixed-value --unset-all`로 제거한다.

#### PowerShell

```powershell
$repo = "C:\dev\project-a\repo-api"
$configPath = "C:/dev/project-a/.gitconfig-scoped"
$matches = @(git -C $repo config --local --fixed-value --get-all include.path $configPath)
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
  throw "include.path 조회 실패: $repo"
}
if ($matches.Count -eq 0) {
  git -C $repo config --local --add include.path $configPath
} elseif ($matches.Count -gt 1) {
  git -C $repo config --local --fixed-value --unset-all include.path $configPath
  if ($LASTEXITCODE -eq 0) {
    git -C $repo config --local --add include.path $configPath
  }
}
if ($LASTEXITCODE -ne 0) { throw "include.path 반영 실패: $repo" }
```

#### POSIX

```bash
repo="/c/dev/project-a/repo-api"
configPath="/c/dev/project-a/.gitconfig-scoped"
if matches="$(git -C "$repo" config --local --fixed-value --get-all include.path "$configPath")"; then
  status=0
else
  status=$?
fi
[ "$status" -eq 0 ] || [ "$status" -eq 1 ] || {
  printf '%s\n' "include.path 조회 실패: $repo" >&2
  exit "$status"
}
count="$(printf '%s\n' "$matches" | awk 'NF { count++ } END { print count + 0 }')"
case "$count" in
  0) git -C "$repo" config --local --add include.path "$configPath" ;;
  1) : ;;
  *)
    git -C "$repo" config --local --fixed-value --unset-all include.path "$configPath" &&
      git -C "$repo" config --local --add include.path "$configPath"
    ;;
esac
```

위 코드는 repo 한 개에 대한 원자 연산 예시다. 실제 일괄 적용에서는 각 명령의 종료 코드를 검사하고, 실패 즉시 아래 롤백을 수행한다.

### 4) 실패 시 전체 롤백

공통 config 생성·교체, repo 로컬 config 쓰기, 값/출처 검증 중 하나라도 실패하면:

1. 추가 repo 처리를 즉시 중단한다.
2. 이미 처리한 repo를 포함해 **모든 대상 repo 로컬 config**를 작업 전 스냅샷 바이트로 복구한다.
3. 공통 config가 원래 존재했으면 기존 바이트로 복구하고, 이번 작업에서 새로 만든 파일이면 그 파일만 제거한다.
4. 각 파일을 다시 byte 비교하고 `git config --local --list`로 구문을 확인한다.
5. 복구 성공/실패와 수동 복구가 필요한 정확한 경로를 보고한다. 복구 실패를 성공으로 숨기지 않는다.

성공한 경우에도 모든 repo의 값·출처와 관리 대상 외 include 보존을 검증한 뒤에만 임시 스냅샷을 정리한다.

---

## [검증]

각 repo에서 실제 적용된 user 정보와 그 **출처 파일**을 확인한다.

### PowerShell

```powershell
git -C "C:\dev\project-a\repo-api" config --show-origin --get user.name
git -C "C:\dev\project-a\repo-api" config --show-origin --get user.email
```

### POSIX

```bash
git -C "/c/dev/project-a/repo-api" config --show-origin --get user.name
git -C "/c/dev/project-a/repo-api" config --show-origin --get user.email
```

### 리포트 형식

`templates/verify-report.md` 구조로 대화창에 표 출력한다.
출처가 공통 config 파일(`.gitconfig-scoped` 등)을 가리키면 정상으로 판정한다.
출처가 전역(`~/.gitconfig`)이면 include가 적용되지 않은 것이므로 경고로 표시한다.

---

## [경로·안전 규칙]

- 전역(`--global`)·시스템(`--system`) 설정은 절대 수정하지 않는다. 항상 `--local`만 쓴다.
- `include.path`에는 슬래시(`/`) 절대경로만 넣는다.
- 기존의 관련 없는 `include.path`를 제거·재정렬하지 않는다. 제거는 승인된 정확한 값에만 `--fixed-value`를 사용한다.
- 공통 config에는 user.name/email만 둔다. 토큰·비밀번호는 넣지 않는다.
- 적용 전 대상 목록을 사용자에게 보여주고 승인 게이트를 통과해야 한다.
- 명령 인자에 경로와 값을 직접 전달하고, 사용자 입력을 셸 코드로 조합하거나 평가하지 않는다.
