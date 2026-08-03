---
name: commit
description: >
  사용자가 Git 커밋 실행 또는 커밋 메시지 작성을 명시적으로 요청할 때만 사용한다.
  "커밋해줘", "git commit 해줘", "이 변경을 커밋해줘", "커밋 메시지를 작성해줘"
  같은 요청에 적용한다. 구현, 수정, 리뷰, 검증 완료만으로 커밋 의도를 추론하지 않는다.
disable-model-invocation: true
---

# Commit workflow

## 권한 경계

- 커밋 메시지만 요청하면 메시지만 제안하고 index, worktree, `HEAD`를 변경하지 말라.
- 실제 커밋 요청이 있을 때만 stage와 `git commit`을 실행하라. 범위가 모호하면 먼저 질문하라.
- 현재 직접 호출 형식은 Codex의 `$commit <범위>`와 Claude Code의
  `/harness-kit:commit <범위>`다. 호출에 적힌 범위를 권한 경계로 사용하라.
- `--no-verify`, `--amend`, push, tag, branch 생성은 각각 별도의 명시적 요청 없이는 수행하지 말라.
- 저장소 정책이나 사용자 요청에 없는 `Co-Authored-By` trailer를 강제하거나 자동 삽입하지 말라.

## 1. 저장소와 변경 증거 확인

1. `git rev-parse --show-toplevel`로 대상 저장소를 확정하라.
2. 대상 경로에 적용되는 `AGENTS.md`와 `CLAUDE.md`를 읽고 커밋 규칙, 금지 작업,
   단일·복수 애플리케이션 구조를 확인하라. 저장소 규칙을 이 스킬의 예시보다 우선하라.
3. 커밋 전 `git rev-parse --verify HEAD`로 `before_sha`를 기록하라. `HEAD`가 아직
   없는 최초 커밋 저장소라면 실패를 오류로 숨기지 말고 `initial commit` 상태로
   기록한 뒤 계속하라.
4. 다음 명령으로 staged, unstaged, untracked 변경과 최근 메시지 관례를 모두 확인하라.

```text
git status --short --branch
git diff --staged --stat
git diff --staged
git diff --stat
git diff
git ls-files --others --exclude-standard
git log -5 --oneline
```

5. Git diff에 나오지 않는 의도한 untracked 파일은 내용을 직접 읽어라. 바이너리와 생성물은
   경로, 크기, 출처를 확인하라.

## 2. 범위를 보존해 stage

1. 사용자 요청을 파일과 논리 변경 단위에 대응시켜 의도한 범위를 목록으로 제시하라.
2. 기존 staged 변경 중 범위 밖 항목이 있으면 그대로 보존하고 중단해 처리 방법을 물어라.
   임의로 unstage하거나 함께 커밋하지 말라.
   다른 사용자의 staged 또는 unstaged 작업을 reset, restore, checkout, stash, drop하지 말라.
3. 기능, 수정, 문서, 리팩터링처럼 독립된 관심사가 섞였으면 분리 커밋을 제안하라.
   한 파일에 서로 다른 관심사가 섞여 안전하게 분리할 수 없으면 사용자 선택을 받아라.
4. 새로 stage할 때는 `git add -- <path...>`처럼 검토한 명시적 경로만 사용하라.
   의도하지 않은 파일이나 hunk를 일괄 stage하지 말라.
5. stage 후 `git status --short`와 `git diff --staged --stat`, `git diff --staged`를
   다시 확인하라. staged diff가 비었거나 범위가 다르면 커밋하지 말고 원인을 보고하라.

## 3. 증거 기반 메시지 작성

저장소 지침과 최근 log의 언어·scope·길이 관례를 따르고 다음 형태의 Conventional Commits
제목과 본문을 작성하라.

```text
<type>(<scope>)!: <subject>

<body>
```

- `type`, 선택적 `scope`, 선택적 `!`를 실제 diff의 성격에 맞춰 선택하라.
- subject에는 가장 중요한 결과를 명확하게 쓰고 body에는 변경 이유, 주요 결정과 영향,
  실제로 실행한 검증 결과를 적어라.
- 실행하지 않은 테스트, 해결하지 않은 문제, diff에 없는 효과를 주장하지 말라.
- breaking change, issue, trailer는 실제 근거나 저장소 규칙이 있을 때만 추가하라.
- 서로 다른 변경을 하나의 모호한 제목으로 숨기지 말라.

필요하면 [examples/commit-messages.md](examples/commit-messages.md)를 참고하라.

## 4. hook을 보존해 커밋

1. 검토한 제목과 body로 일반 `git commit`을 실행해 저장소 hook을 그대로 통과시켜라.
2. hook 실패 시 종료 코드와 핵심 출력을 보고하고 status와 diff를 다시 확인하라. hook이
   파일을 수정했을 수 있으므로 변경 범위를 재검토하고 `--no-verify`로 우회하지 말라.
3. 빈 stage, 범위 모호성, 커밋 실패를 성공으로 보고하지 말라. 원인을 설명하고 필요한
   사용자 결정 또는 수정만 요청하라.
4. 실패 후 자동으로 `--amend`하거나 새 commit을 반복 생성하지 말라.

## 5. 결과 검증과 보고

성공 후 다음 증거를 확인하라.

```text
git rev-parse HEAD
git show --format=fuller --stat --summary <commit-sha>
git status --short --branch
git diff --staged
git diff --stat
git ls-files --others --exclude-standard
```

- 기존 `HEAD`가 있었다면 새 SHA가 `before_sha`와 다른지 확인하라. 최초 커밋이었다면
  새 `HEAD`가 생성됐는지 확인하고, 두 경우 모두 `git show`의 메시지와 파일이 의도한
  범위인지 확인하라.
- commit SHA, 제목과 body 요약, 포함 파일, hook·검증 결과를 보고하라.
- 남은 staged, unstaged, untracked 변경을 구분해 보고하라. 남은 변경을 숨기거나 자동으로
  추가 커밋하지 말라.
