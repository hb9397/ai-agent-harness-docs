# 설정과 서명 정책 스키마

## 설정 입력

Plan과 Apply에 전달하는 JSON은 비밀정보를 담지 않는다.

```json
{
  "schema_version": "1.0.0",
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
      "id": "dev-user",
      "role": "developer",
      "accounts": {
        "github": "@dev-user",
        "gitlab": "@dev-user",
        "gitea": "@dev-user"
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
      "pattern": ".docs/fe-exam-portal/impl-doc/dev-user/**",
      "minimum_role": "developer",
      "priority": 100,
      "owner": "dev-user"
    }
  ],
  "enable_git_hooks": true,
  "enable_ai_hooks": true
}
```

규칙:

- `project_id`, 애플리케이션, principal `id`는 경로 구분자로 쓸 수 없는 안전한
  식별자여야 한다.
- 역할은 `admin`, `pm-pl`, `developer`만 사용한다.
- principal ID는 중복될 수 없다. 최초 설정에는 admin이 정확히 한 명 이상 있어야 한다.
- provider 계정은 `@user` 또는 `@org/team` 형식이다. 토큰·비밀번호는 금지한다.
- `protected_branches`는 프로젝트가 이미 정한 값만 넣는다. 빈 목록은 서버 규칙을
  만들지 않는다는 뜻이다.
- 복수 저장소에서 `.docs`가 별도 Git 저장소면 repository `path`는 `.docs`다.
- `path_rules`를 생략하면 애플리케이션과 principal을 기준으로 기본 규칙을 제안한다.
  프로젝트가 규칙을 확정하면 같은 필드에 명시해 서명 정책의 정본으로 사용한다.
- 생성기는 명시 규칙에 잡히지 않은 새 보호 문서도 관리자만 쓸 수 있도록 낮은
  우선순위의 `AGENTS.md`, `CLAUDE.md`, `.docs/**` 관리자 기본 규칙을 서명 정책에
  포함한다. 명시 규칙은 이 기본값보다 높은 우선순위로 범위를 위임한다.
- `priority`가 높은 규칙이 먼저 적용된다. `owner`가 있는 developer 규칙은 해당
  principal과 상속받은 상위 역할만 허용한다.

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

`policy.json`에는 역할 상속, principal과 provider 계정, 경로 규칙,
`policy_core_sha256`, `generated_manifest_sha256`가 들어간다. 경로 규칙은 우선순위가
높은 규칙부터 평가하며 같은 역할에서는 개발자 `owner`가 일치해야 개인 경로에 쓸 수
있다.

`generated-manifest.json`은 파일 전체를 소유하는 항목은 full hash, 사용자 본문과
공존하는 CODEOWNERS·instruction은 관리 블록 hash로 추적한다. manifest 파일 자체와
서명 파일은 순환을 피하려고 목록에서 제외하고 `policy.json`이 manifest hash를
서명 범위에 포함한다.

## 역할 상속

```text
admin > pm-pl > developer
```

- admin: 하네스 배선, 권한 정책과 관리 블록, 하위 역할 범위
- pm-pl: 앱 설계·컨텍스트·instruction 본문, developer 범위
- developer: 자신의 `impl-doc/{사용자}/**`, 승인된 prototype·inbox 제안 경로

경로는 스크립트 내부의 역할 이름만으로 허용하지 않는다. 서명된 `path_rules`와
principal 소유자 바인딩을 읽는다.
