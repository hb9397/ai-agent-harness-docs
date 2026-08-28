# 설정과 서명 정책 스키마

## 설정 입력

Plan과 Apply에 전달하는 JSON은 비밀정보를 담지 않는다.

```json
{
  "schema_version": "1.1.0",
  "project_id": "example-project",
  "applications": ["fe-exam-portal", "fe-exam-mobile", "be-exam-portal"],
  "principals": [
    {
      "id": "admin-user",
      "role": "admin",
      "accounts": {
        "github": "@admin-user",
        "gitlab": "@admin-user",
        "gitea": "@admin-user"
      }
    },
    {
      "id": "project-lead",
      "role": "pm-pl",
      "accounts": {
        "github": "@project-lead",
        "gitlab": "@project-lead",
        "gitea": "@project-lead"
      }
    },
    {
      "id": "mobile-doc-lead",
      "role": "app-doc-lead",
      "applications": ["fe-exam-mobile"],
      "accounts": {
        "github": "@mobile-doc-lead",
        "gitlab": "@mobile-doc-lead",
        "gitea": "@mobile-doc-lead"
      }
    }
  ],
  "repositories": [
    {
      "path": ".",
      "provider": "github",
      "protected_branches": ["main"],
      "server_policy": "externally-approved"
    }
  ],
  "path_rules": [
    {
      "pattern": ".docs/fe-exam-mobile/context-base/**",
      "write_scope": "app-doc",
      "application": "fe-exam-mobile",
      "priority": 100
    },
    {
      "pattern": ".docs/fe-exam-mobile/impl-doc/**",
      "write_scope": "team",
      "priority": 100
    }
  ],
  "enable_git_hooks": true,
  "enable_ai_hooks": true
}
```

규칙:

- `project_id`, 애플리케이션, principal `id`는 경로 구분자로 쓸 수 없는 안전한
  식별자여야 한다.
- 역할은 `admin`, `pm-pl`, `app-doc-lead`만 사용한다. 개발자는 역할 principal로
  등록하지 않는다.
- principal ID는 중복될 수 없다. 최초 설정에는 admin이 한 명 이상 있어야 한다.
- 같은 provider 계정을 둘 이상의 principal에 중복 연결할 수 없다.
- `app-doc-lead`에는 설정된 애플리케이션 중 하나 이상을 `applications`로 배정한다.
  `admin`과 `pm-pl`은 전역 역할이므로 이 필드를 두지 않는다.
- provider 계정은 `@user` 또는 `@org/team` 형식이다. 토큰·비밀번호는 금지한다.
- `protected_branches`는 프로젝트가 이미 정한 값만 넣는다. 빈 목록은 서버 규칙을
  만들지 않는다는 뜻이다.
- 복수 저장소에서 `.docs`가 별도 Git 저장소면 repository `path`는 `.docs`다.
- `path_rules`를 생략하면 애플리케이션과 문서 종류를 기준으로 기본 규칙을 제안한다.
  프로젝트가 규칙을 확정하면 같은 필드에 명시해 서명 정책의 정본으로 사용한다.
- 생성기는 명시 규칙에 잡히지 않은 새 보호 문서도 관리자만 쓸 수 있도록 낮은
  우선순위의 `AGENTS.md`, `CLAUDE.md`, `.docs/**` 관리자 기본 규칙을 서명 정책에
  포함한다. 명시 규칙은 이 기본값보다 높은 우선순위로 범위를 위임한다.
- `write_scope`는 `admin`, `app-doc`, `team` 중 하나다. `app-doc`에는 반드시 대상
  애플리케이션을 함께 적는다.
- `priority`가 높은 규칙이 먼저 적용된다. `team`은 역할 등록이 없는 일반 기여자도
  허용하며 실제 저장소 쓰기 권한은 Git 서비스와 저장소 설정이 맡는다.

## 공유 산출물

```text
.docs/harness/access-control/
├── trust.json
├── policy.json
├── policy.sig
├── provider-state.json
├── generated-manifest.json
└── hooks/
    ├── write_access_guard.py
    └── git/
        ├── pre-commit
        └── pre-push
```

`policy.json`에는 역할 상속, 앱별 역할 배정, principal과 provider 계정, 경로별 쓰기
범위, `policy_core_sha256`, `generated_manifest_sha256`가 들어간다. 경로 규칙은
우선순위가 높은 규칙부터 평가한다.

`generated-manifest.json`은 파일 전체를 소유하는 항목은 full hash, 사용자 본문과
공존하는 CODEOWNERS·instruction은 관리 블록 hash로 추적한다. manifest 파일 자체와
서명 파일은 순환을 피하려고 목록에서 제외하고 `policy.json`이 manifest hash를
서명 범위에 포함한다.

## 역할과 쓰기 범위

```text
admin > pm-pl
app-doc-lead = 배정된 앱 안에서만 pm-pl과 같은 문서 권한
등록되지 않은 일반 기여자 = team 범위
```

- `admin`: 하네스 배선, 권한 정책과 관리 블록, 루트 지도, CODEOWNERS와 훅 설정
- `pm-pl`: 모든 앱의 설계·컨텍스트·instruction 본문
- `app-doc-lead`: 배정된 앱의 설계·컨텍스트·instruction 본문
- `team`: 단일 앱 `.docs/impl-doc/**`, 복수 앱 `.docs/{앱}/impl-doc/**`, 승인된
  prototype과 `_inbox` 경로

`admin`은 `app-doc` 쓰기도 허용되지만 AI는 편집 직전에 대상 앱·파일·원래 소유
범위·수정 이유를 보여주고 별도 확인을 받아야 한다. 활성으로 검증된 AI 훅은
`permissionDecision=ask`를 반환한다. 이 확인은 일반 내용 승인과 분리한다. 표준 Git
훅은 비대화형이므로 질문 자체를 강제하지 못하고 역할에 따른 허용·거부만 판정한다.

경로는 스크립트 내부 역할 이름만으로 허용하지 않는다. 서명된 `path_rules`, principal
역할과 앱 배정을 함께 읽는다.
