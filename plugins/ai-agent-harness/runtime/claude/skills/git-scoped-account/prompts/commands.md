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

승인 후에만 실행한다. 두 단계로 나뉜다.

### 1) 공통 config 파일 생성

`templates/gitconfig-shared.md` 구조로 프로젝트 최상위(컨테이너) 디렉토리에 파일을 만든다.
파일이 이미 있으면 기존 내용을 먼저 보여주고 덮어쓸지 다시 확인받는다.

### 2) 각 repo에 include.path 주입

`include.path` 값은 **공통 config 파일의 절대경로**이며, 슬래시(`/`)를 사용한다.
git config 값에서는 역슬래시가 이스케이프 문자로 해석되므로 Windows 경로도 `/`로 변환한다.

#### PowerShell

```powershell
$base       = "C:\dev\project-a"
$configPath = "C:/dev/project-a/.gitconfig-scoped"   # 슬래시 경로

Get-ChildItem -LiteralPath $base -Directory |
  Where-Object { Test-Path (Join-Path $_.FullName ".git") } |
  ForEach-Object {
    git -C $_.FullName config --local include.path $configPath
  }
```

#### POSIX

```bash
base="/c/dev/project-a"
configPath="/c/dev/project-a/.gitconfig-scoped"
for d in "$base"/*/; do
  [ -e "$d/.git" ] && git -C "${d%/}" config --local include.path "$configPath"
done
```

> 멱등성: 동일 `include.path`가 이미 있으면 git이 같은 키를 중복 추가할 수 있다.
> 재적용 시 `git -C <repo> config --local --get-all include.path`로 기존 값을 확인하고,
> 중복이면 `--unset-all include.path` 후 다시 추가한다.

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
- 공통 config에는 user.name/email만 둔다. 토큰·비밀번호는 넣지 않는다.
- 적용 전 대상 목록을 사용자에게 보여주고 승인 게이트를 통과해야 한다.
