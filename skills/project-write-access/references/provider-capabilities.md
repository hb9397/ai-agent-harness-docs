# Git 서비스와 host 지원 범위

필요한 provider·host 섹션만 읽는다. 이 문서는 CODEOWNERS 동작, 참여자 조회와 외부
관리 정책의 한계를 확인하기 위한 참고 자료다. `project-write-access`는 원격 브랜치
보호·검토·병합 설정을 변경하지 않는다. 프로젝트 관리자가 서비스 설정을 별도로
운영할 때는 요금제와 설치 버전에 맞는 공식 문서를 다시 확인한다.

생성기는 `admin`과 `app-doc`처럼 명시적인 문서 소유자가 있는 경로만 CODEOWNERS
관리 블록에 넣는다. 역할 등록이 없는 일반 기여자에게 열린 `team` 경로에는 owner
규칙을 만들지 않는다. 그래서 `.ai-docs/**` 전체 관리자 fallback도 CODEOWNERS에는 넣지
않고, 알려지지 않은 새 `.ai-docs` 경로의 기본 관리자 판정은 서명 정책과 로컬·AI 가드가
맡는다. 새 경로의 원격 승인까지 강제하려면 정책에 명시 경로를 추가해야 한다.

## GitHub

- CODEOWNERS 탐색 순서: `.github/CODEOWNERS` → 루트 `CODEOWNERS` →
  `docs/CODEOWNERS`. 첫 파일만 사용한다.
- PR에서 code owner 승인을 요구하려면 브랜치 보호 또는 ruleset의 해당 규칙이
  필요하다.
- code owner 사용자·팀은 저장소 write 권한이 있어야 한다.
- 서버 설정 조회·변경에는 저장소 관리자 권한과 API 인증이 필요하지만, 이 스킬은
  참여자·호출자 권한 조회만 수행하고 설정 변경 API는 호출하지 않는다.
- 참여자는 `List repository collaborators`의 `affiliation=all`과 유효 permission으로
  조회한다. 조직·팀을 통해 접근한 사용자도 결과에 포함되며 페이지를 끝까지 읽는다.

공식 자료:

- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- https://docs.github.com/en/rest/branches/branch-protection
- https://docs.github.com/en/rest/collaborators/collaborators

## GitLab

- CODEOWNERS 탐색 순서: 루트 `CODEOWNERS` → `docs/CODEOWNERS` →
  `.gitlab/CODEOWNERS`. 첫 파일만 사용한다.
- Code Owner 승인을 강제하려면 target branch가 protected이고 Code Owner approval이
  활성화돼야 한다.
- 기능은 GitLab tier·self-managed 버전에 따라 다르다. 공식 문서의 현재 tier 표를
  확인한다.
- `Allowed to push and merge` 사용자는 MR 승인을 우회할 수 있으므로 직접 push 권한도
  함께 확인한다.
- 참여자는 `/projects/:id/members/all`로 조회해 직접 구성원뿐 아니라 초대 그룹과 상위
  그룹에서 상속된 유효 구성원까지 확인한다.

공식 자료:

- https://docs.gitlab.com/user/project/codeowners/
- https://docs.gitlab.com/user/project/repository/branches/protected/
- https://docs.gitlab.com/api/protected_branches/
- https://docs.gitlab.com/api/project_members/

## Gitea

- CODEOWNERS 탐색 순서: 루트 `CODEOWNERS` → `docs/CODEOWNERS` →
  `.gitea/CODEOWNERS`. 첫 파일만 사용한다.
- 패턴은 GitHub·GitLab glob이 아니라 Go 정규식이다.
- Gitea는 적용 가능한 규칙을 조합하므로 GitHub·GitLab식 전체 fallback과 뒤쪽 override를
  그대로 쓰면 admin 승인까지 중복 요구할 수 있다. 생성기는 서명 정책에 열거된 경로만
  정규식으로 만들며, 새 `.ai-docs` 경로는 정책에 추가하기 전까지 원격 CODEOWNERS 완전
  보호 대상으로 주장하지 않는다.
- branch protection에서 code owner approval을 켜야 PR 병합 제한이 생긴다.
- 저장소 소유자·관리자 권한과 API 토큰이 있어야 서버 규칙을 조회·변경할 수 있다.
  프로젝트 관리자가 별도로 설정할 때는 설치 버전의 OpenAPI에서
  `block_on_codeowner_reviews`, push·merge allowlist 필드 지원을 확인한다. 이 스킬은
  해당 변경 API를 호출하지 않는다.
- 참여자는 collaborator, 저장소에 연결된 team과 team member, 사용자별 repository
  permission을 합쳐 조회한다. team 목록만 사람 목록으로 사용하지 않는다.

공식 자료:

- https://docs.gitea.com/next/usage/repository/code-owners/
- https://docs.gitea.com/api/next/operations/repo-get-branch-protection/
- https://docs.gitea.com/usage/access-control/protected-branches
- https://docs.gitea.com/api/next/operations/repo-list-collaborators/
- https://docs.gitea.com/api/next/operations/repo-list-teams/
- https://docs.gitea.com/api/operations/repo-get-repo-permissions/

## 참여자 조회 공통 규칙

- 커밋·푸시·PR·MR 작성자 이력은 현재 접근 권한을 나타내지 않으므로 역할 후보의 정본으로
  사용하지 않는다.
- 루트 라우팅 정본에 등록된 모든 repository를 조회한다. 한 앱이나 한 저장소만 보고
  프로젝트 전체 참여자라고 표현하지 않는다.
- provider·host·불변 account ID로 합치고, ID가 없을 때만 login을 보조 식별자로 쓴다.
- bot·서비스 계정, 비활성 계정, 읽기 전용 계정을 숨기지 않는다. 관리자가 역할 배정
  대상에서 포함하거나 제외한다.
- 조회 권한이나 API가 부족해 일부가 누락되면 `partial`로 보고하고 자동 역할 배정을
  중단한다.
- 스킬 번들의 Python 코드가 직접 네트워크 연결이나 토큰 처리를 하지 않는다. GitHub는
  `gh api`, GitLab은 `glab api`, Gitea는 `tea api`의 인증된 프로필을 통해 읽는다.
  CLI가 없거나 host 인증이 안 되어 있으면 해당 저장소를 실패 범위로 표시한다.

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
