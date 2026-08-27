# Git 서비스와 host 지원 범위

필요한 provider·host 섹션만 읽는다. 기능은 서비스 요금제와 설치 버전에 따라 달라질
수 있으므로 Apply 직전에 공식 문서를 다시 확인한다.

## GitHub

- CODEOWNERS 탐색 순서: `.github/CODEOWNERS` → 루트 `CODEOWNERS` →
  `docs/CODEOWNERS`. 첫 파일만 사용한다.
- PR에서 code owner 승인을 요구하려면 브랜치 보호 또는 ruleset의 해당 규칙이
  필요하다.
- code owner 사용자·팀은 저장소 write 권한이 있어야 한다.
- 서버 설정 조회·변경은 저장소 관리자 권한과 API 인증이 필요하다.

공식 자료:

- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- https://docs.github.com/en/rest/branches/branch-protection

## GitLab

- CODEOWNERS 탐색 순서: 루트 `CODEOWNERS` → `docs/CODEOWNERS` →
  `.gitlab/CODEOWNERS`. 첫 파일만 사용한다.
- Code Owner 승인을 강제하려면 target branch가 protected이고 Code Owner approval이
  활성화돼야 한다.
- 기능은 GitLab tier·self-managed 버전에 따라 다르다. 공식 문서의 현재 tier 표를
  확인한다.
- `Allowed to push and merge` 사용자는 MR 승인을 우회할 수 있으므로 직접 push 권한도
  함께 확인한다.

공식 자료:

- https://docs.gitlab.com/user/project/codeowners/
- https://docs.gitlab.com/user/project/repository/branches/protected/
- https://docs.gitlab.com/api/protected_branches/

## Gitea

- CODEOWNERS 탐색 순서: 루트 `CODEOWNERS` → `docs/CODEOWNERS` →
  `.gitea/CODEOWNERS`. 첫 파일만 사용한다.
- 패턴은 GitHub·GitLab glob이 아니라 Go 정규식이다.
- Gitea는 적용 가능한 규칙을 조합하므로 GitHub·GitLab식 전체 fallback과 뒤쪽 override를
  그대로 쓰면 admin 승인까지 중복 요구할 수 있다. 생성기는 서명 정책에 열거된 경로만
  정규식으로 만들며, 새 `.docs` 경로는 정책에 추가하기 전까지 원격 CODEOWNERS 완전
  보호 대상으로 주장하지 않는다.
- branch protection에서 code owner approval을 켜야 PR 병합 제한이 생긴다.
- 저장소 소유자·관리자 권한과 API 토큰이 필요하다. 설치 버전의 OpenAPI에서
  `block_on_codeowner_reviews`, push·merge allowlist 필드 지원을 확인한다.

공식 자료:

- https://docs.gitea.com/next/usage/repository/code-owners/
- https://docs.gitea.com/api/next/operations/repo-get-branch-protection/
- https://docs.gitea.com/usage/access-control/protected-branches

## 표준 Git 훅

- `pre-commit`은 commit 전에 실행되고 non-zero로 중단할 수 있다.
- `pre-push`는 push할 ref를 stdin으로 받고 non-zero로 push를 중단할 수 있다.
- `core.hooksPath`로 훅 디렉토리를 바꿀 수 있다.
- `pre-add`는 없고 `--no-verify` 등으로 로컬 훅을 우회할 수 있다.

공식 자료:

- https://git-scm.com/docs/githooks
- https://git-scm.com/docs/gitfaq

## Claude Code

- 프로젝트 공유 설정은 `.claude/settings.json`이다.
- `PreToolUse` command hook은 도구 호출 JSON을 stdin으로 받고 차단 결정을 반환할 수
  있다.
- `${CLAUDE_PROJECT_DIR}`는 세션 시작 프로젝트를 가리키며 worktree에서는 hook 입력의
  `cwd`를 함께 확인해야 한다.
- 프로젝트 설정은 사용자가 바꿀 수 있다. 조직에서 강제하려면 managed settings 같은
  상위 계층을 별도로 사용한다.

공식 자료:

- https://code.claude.com/docs/en/hooks
- https://docs.anthropic.com/ko/docs/claude-code/iam

## Codex

이 저장소의 현재 host 기준선은 프로젝트 `.codex/hooks.json`의 `PreToolUse`와 사용자
훅 검토를 사용한다. 설치 직후 상태는 `pending-trust`로 기록하고 사용자가 실제 hook
목록과 스크립트 hash를 검토한 증적이 있어야 active로 바꾼다.

공개 공식 문서에서 현재 프로젝트 훅 계약을 확인할 수 없는 환경에서는 instruction과
표준 Git 훅만 적용하고 Codex host hook은 `검증 불가`로 둔다. 다른 제품의 hook JSON을
Codex에 그대로 복사해 지원된다고 주장하지 않는다.
