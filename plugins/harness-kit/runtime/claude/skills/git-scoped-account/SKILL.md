---
name: git-scoped-account
description: "사용자가 git 계정 적용 또는 출처 확인을 명시적으로 요청했을 때만 사용한다. 전역 ~/.gitconfig를 건드리지 않고, git으로 관리하지 않는 프로젝트 최상위 폴더 바로 아래의 애플리케이션 git repo들에 공통 git 계정(user.name/email)을 include.path 방식으로 일괄 적용·확인한다. '이 폴더 아래 repo들 git 계정 한 번에 바꿔줘', '프로젝트마다 git 계정이 달라서 이 트리에만 적용', '전역 설정 안 건드리고 하위 repo user.name/email 일괄 설정/확인', 'gitea/gitlab/github 계정 디렉토리별로 분리' 같은 명시 요청에 사용한다."
allowed-tools: Read, Write
disable-model-invocation: true
---

# git-scoped-account

사용자가 계정 적용 또는 상태 확인을 명시적으로 요청한 경우에만 실행한다. 일반 git 작업,
리뷰, 검증 요청에서 계정 변경 의도를 추론하지 않는다.

이 스킬은 명시 호출 전용이다. Codex에서는 `$git-scoped-account`, Claude
Code에서는 `/harness-kit:git-scoped-account`를 호출하고 적용 또는 확인
범위를 함께 적는다.

전역 `~/.gitconfig`는 그대로 두고, git으로 관리하지 않는 프로젝트 최상위 폴더 바로 아래의 애플리케이션 git repo들이
공통 계정 설정 파일을 `include.path`로 참조하게 만들어, 그 프로젝트 폴더의 하위 repo들에만 git 계정을 일괄 적용한다.

명령은 사용자 환경(win32/PowerShell 우선, POSIX 대안)에 맞춰 실행한다.
세부 명령·탐지·검증 로직은 `prompts/commands.md`에 있다. 이 파일에는 흐름만 둔다.

---

## 진입 분기

| 상황 | 이동할 Step |
|------|------------|
| 계정 적용/변경 요청 | Step 1 → 2 → 3 → 4 → 5 |
| 현재 적용 상태만 확인 | Step 5 (검증만 실행) |

---

## Step 1 — 입력 수집

프로젝트 최상위(컨테이너) 디렉토리 경로 + 적용할 `user.name` / `user.email`를 확보한다.
대화·인자에서 추론 가능하면 묻지 않는다. 불명확한 항목만 묻는다.
질문 우선순위는 `prompts/commands.md`의 [입력 수집] 섹션을 참조한다.

---

## Step 2 — 애플리케이션 repo 탐지 (적용 대상 목록화)

프로젝트 최상위(컨테이너) 디렉토리 자체는 적용 대상이 아니다. 바로 아래 **1단계** 폴더 중 `.git`을 가진 애플리케이션 repo만 포함한다.
탐지 명령은 `prompts/commands.md`의 [탐지] 섹션을 참조한다.

> 중첩(2단계 이상) repo는 의도적으로 제외한다. 바로 아래에서 탐지 결과가 0건이면 이유와 함께 종료한다.

---

## Step 3 — 적용 계획 확인

공통 config 파일 경로, 적용할 user 정보, 대상 repo 목록을 표로 보여준다.

> ✋ **확인 게이트**
> "위 {N}개 repo에 공통 계정 설정을 적용할까요? (승인 / 수정 / 취소)"
> **승인 전에는 어떤 파일도 생성·수정하지 않는다.**

---

## Step 4 — 적용 (승인 후에만 실행)

세부 명령은 `prompts/commands.md`의 [적용] 섹션을 참조한다.

1. 프로젝트 최상위(컨테이너) 디렉토리에 공통 config 파일을 생성한다. 구조는 `templates/gitconfig-shared.md` 참조.
   - 이미 존재하면 덮어쓰기 전 내용을 보여주고 다시 확인받는다.
2. 변경 전에 공통 config와 모든 대상 repo의 실제 로컬 config 파일을 임시 백업에 **byte 단위로 스냅샷**한다.
3. 대상 repo 각각의 로컬 config에 `include.path`(공통 파일의 절대경로)를 주입한다.
   - 같은 값만 정확히 비교해 0개면 추가, 1개면 유지, 2개 이상이면 그 값만 제거 후 1개를 다시 추가한다.
   - 다른 `include.path` 값은 순서와 내용을 포함해 보존한다.
4. 한 repo라도 쓰기 또는 검증에 실패하면 이미 바꾼 repo와 공통 config를 스냅샷으로 전부 복구하고, 복구 검증 결과를 보고한다.
5. 모든 검증이 성공한 뒤에만 임시 백업을 정리한다.

---

## Step 5 — 검증 리포트

각 repo에서 `git config --show-origin --get user.name / user.email`로 출처와 값을 확인한다.
검증 명령·리포트 형식은 `prompts/commands.md`의 [검증] 섹션을 참조한다.

결과는 대화창에 표로 출력한다. (별도 파일 저장은 사용자 요청 시에만)
