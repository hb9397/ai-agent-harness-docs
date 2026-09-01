# 설정과 서명 정책 스키마

## 설정 입력

Plan과 Apply에 전달하는 JSON은 비밀정보를 담지 않는다. `subjects`는 사람·서비스
계정의 정체성을, `role_assignments`는 그 정체성이 맡는 역할을 나타낸다. 둘을 분리해
한 사람이 여러 역할을 맡거나 여러 Git 서비스 계정을 하나의 사람으로 묶을 수 있다.

스키마 `3.0.0`의 문서 루트는 `.ai-docs/`로 고정한다. 이전 `.docs/` 경로의 규칙은
허용하지 않으며, 두 루트를 동시에 운영하지 않는다. 실제 배포본의 `1.1.0`과 정본
전환 과정의 `2.0.0` 서명 정책은 관리자 확인을 거친
`migrate-root-plan`·`migrate-root` 대상으로 분류한다. 그 밖의 이전 스키마나 일부만
남은 정책은 자동 변환하지 않는다.

`1.1.0` 정책에는 Git 서비스 host와 불변 계정 ID가 없으므로, 이관 시에는 서명에 쓰인
관리자 키와 provider·login이 모두 일치해야 한다. 이관 결과인 `3.0.0` 정책은 현재
설정에서 확인한 provider·host·login과 가능한 경우 불변 계정 ID로 계정을 다시 묶는다.

```json
{
  "schema_version": "3.0.0",
  "project_id": "example-project",
  "applications": ["fe-exam-portal", "fe-exam-mobile", "be-exam-portal"],
  "subjects": [
    {
      "id": "owner",
      "accounts": [
        {"provider": "github", "host": "github.com", "account_id": "101", "login": "@owner"},
        {"provider": "gitlab", "host": "gitlab.example.com", "account_id": "202", "login": "@owner"},
        {"provider": "gitea", "host": "git.example.com:3000", "account_id": "303", "login": "@owner"}
      ]
    },
    {
      "id": "mobile-lead",
      "accounts": [
        {"provider": "github", "host": "github.com", "account_id": "404", "login": "@mobile-lead"}
      ]
    },
    {
      "id": "developer-a",
      "accounts": [
        {"provider": "github", "host": "github.com", "account_id": "505", "login": "@developer-a"}
      ]
    }
  ],
  "role_assignments": [
    {"subject_id": "owner", "role": "admin"},
    {"subject_id": "owner", "role": "pm-pl"},
    {"subject_id": "mobile-lead", "role": "app-doc-lead", "applications": ["fe-exam-mobile"]},
    {"subject_id": "developer-a", "role": "developer"}
  ],
  "repositories": [
    {
      "id": "docs-repo",
      "provider": "gitea",
      "host": "git.example.com:3000",
      "cli_login": "keai-gitea",
      "owner": "example",
      "name": "example-docs",
      "purpose": "docs",
      "applications": ["fe-exam-portal", "fe-exam-mobile", "be-exam-portal"],
      "protected_branches": ["main"],
      "server_policy": "externally-approved"
    },
    {
      "id": "mobile-repo",
      "provider": "github",
      "host": "github.com",
      "owner": "example",
      "name": "fe-exam-mobile",
      "purpose": "source",
      "applications": ["fe-exam-mobile"],
      "protected_branches": [],
      "server_policy": "none"
    }
  ],
  "path_rules": [
    {
      "pattern": ".ai-docs/fe-exam-mobile/context-base/**",
      "write_scope": "app-doc",
      "application": "fe-exam-mobile",
      "priority": 100
    },
    {
      "pattern": ".ai-docs/fe-exam-mobile/impl-doc/**",
      "write_scope": "team",
      "priority": 100
    }
  ],
  "local_identity": {
    "provider": "gitea",
    "host": "git.example.com:3000",
    "account": "@owner"
  },
  "enable_git_hooks": true,
  "enable_ai_hooks": true
}
```

규칙:

- `project_id`, 애플리케이션, subject·repository `id`는 안전한 식별자여야 한다.
- 역할은 `admin`, `pm-pl`, `app-doc-lead`, `developer`다. 역할은 상속하지 않는다.
- 한 subject에는 서로 다른 역할을 여러 개 배정할 수 있다. 같은 역할을 중복 배정하지
  않는다.
- 최초 설정에는 명시적 `admin` 배정이 한 명 이상 있어야 하며 `local_identity`가 그
  관리자 계정과 일치해야 한다. 이후 Apply도 현재 관리자 키로 기존 정책을 검증한다.
- 최초 설정·정책 변경·문서 루트 이관의 `local_identity`는 현재 Git 경계에
  `git-scoped-account`가 기록한 provider·host·account와 일치해야 한다. 기존 정책에
  참여자 PC만 연결하는 `local-enroll`은 설정 JSON 없이 이 로컬 표식을 사용한다.
- provider 계정은 `@개인계정`만 사용한다. 팀이나 그룹을 사람 계정처럼 등록하지 않는다.
  같은 provider·host·불변 account ID 조합은 둘 이상의 subject에 연결할 수 없다.
- `account_id`는 가능하면 서비스 API가 주는 불변 ID를 쓴다. 없으면 host와 login으로
  대조하되 이후 조회에서 ID를 얻으면 정책 갱신 대상으로 제안한다.
- `app-doc-lead`에만 설정된 앱 하나 이상을 `applications`로 배정한다. 다른 역할에는
  앱 목록을 두지 않는다.
- `developer`는 참여자를 명시적으로 보여주기 위한 표기다. 배정하지 않았다는 이유로
  앱 소스 코드나 `team` 문서 범위를 차단하지 않는다.
- repository는 논리 프로젝트에 속한 모든 형상관리 단위를 기록한다. 저장소 수는 앱
  수보다 많을 수 있다. `purpose=docs`의 `protected_branches`와 `server_policy`는
  프로젝트 관리자가 외부에서 정한 원격 정책을 설명하는 메타데이터일 뿐, 스킬이 적용할
  명령이 아니다. source 저장소는 참여자 조회와 앱 매핑에 사용한다.
- Gitea repository의 `cli_login`은 해당 host로 인증된 `tea` 로그인 프로필 이름이다.
  토큰이 아니며 저장소마다 다른 프로필을 쓸 수 있다. 없으면 Gitea 참여자 조회는
  실패 범위로 보고하되 기존 정책을 추측으로 채우지 않는다.
- `protected_branches`는 프로젝트가 이미 정한 값만 기록한다. 스킬이 `dev`·`main`
  정책이나 PR·MR 병합 방식을 새로 정하거나 원격 서비스에 적용하지 않는다.
- `path_rules`를 생략하면 앱과 문서 종류를 기준으로 기본 규칙을 만든다. 명시 규칙에
  잡히지 않은 새 `.ai-docs` 보호 문서는 낮은 우선순위의 admin 기본 규칙이 맡는다.
- `write_scope`는 `admin`, `app-doc`, `team`이다. `app-doc`에는 대상 앱을 함께 적는다.
- `priority`가 높은 규칙이 먼저 적용된다. `team`은 역할 등록이 없는 저장소 작성자도
  허용한다.

## 참여자 조회와 역할 선택

`discover-participants`는 커밋·푸시·PR·MR 활동 이력이 아니라 각 저장소의 현재 접근
명단을 조회한다.

```text
python {skill-root}/scripts/project_write_access.py discover-participants \
  --config {config-json}
```

- GitHub는 저장소의 모든 유효 collaborator와 권한을 조회한다.
- GitLab은 `/members/all`로 직접·상속·초대·상위 그룹의 유효 구성원을 조회한다.
- Gitea는 collaborator, 저장소 team, 사용자별 유효 permission을 합친다.
- Python 네트워크 모듈이나 설정 JSON 속 토큰을 사용하지 않는다. 인증된 `gh api`,
  `glab api`, `tea api`가 각 host의 자격 증명 저장소를 사용한다.
- 모든 repository를 조회하고 provider·host·불변 account ID 기준으로 합친다.
- bot, 비활성 계정, 읽기 전용 계정을 숨기지 않고 별도로 표시한다.
- 결과가 partial 또는 failed면 누락 저장소를 알리고, 추측으로 역할을 배정하지 않는다.
- 관리자가 `admin`, `pm-pl`, 앱별 `app-doc-lead`를 직접 고르고 `developer`는 포함할
  계정 또는 제외할 계정 목록으로 일괄 선택한다. 조회 자체는 아무 역할도 부여하지 않는다.

## 공유 산출물

```text
.ai-docs/harness/access-control/
├── trust.json
├── policy.json
├── policy.sig
├── provider-state.json
├── generated-manifest.json
├── write-access-instruction.md
└── hooks/
    ├── write_access_guard.py
    └── git/
        ├── pre-commit
        └── pre-push
```

`policy.json`에는 subject, 명시적 역할 배정, 앱·repository 매핑, 경로별 쓰기 범위와
생성 목록 해시가 들어간다. `generated-manifest.json`은 파일 전체 또는 관리 블록의
해시를 추적한다. 루트 `AGENTS.md`·`CLAUDE.md`에는 전용
`write-access-instruction.md`를 반드시 읽으라는 짧은 관리 블록만 넣는다. 앱별
instruction 본문에 권한 계약을 복제하지 않는다.

## 역할과 쓰기 범위

```text
admin          = 루트 컨텍스트·harness·CODEOWNERS·권한 설정
pm-pl          = 모든 앱의 설계·컨텍스트·instruction
app-doc-lead   = 배정된 앱의 설계·컨텍스트·instruction
developer      = 일반 기여자 명시 표기, 별도 쓰기 권한 없음
미등록 작성자 = team 범위
```

`admin`은 `pm-pl`을 상속하지 않는다. 같은 사람이 두 범위를 모두 맡으면 두 역할을
각각 배정한다. 권한이 있는 `pm-pl` 또는 app-doc-lead라도 AI가 앱 핵심 문서를 쓰기
직전에 대상 앱·파일, 문서 종류와 역할, 수정 요약·이유, 현재 역할을 설명하고 별도
승인을 받는다. 표준 Git 훅은 비대화형이므로 승인 질문이 아니라 권한 판정만 수행한다.
