# prompts/update-mode.md
# 역할: 이미 세팅된 프로젝트에서 .ai-docs·루트 컨텍스트를 갱신하는 절차

---

## 전제

- SKILL.md Step 3에서 **갱신 모드**로 판정.
- `.ai-docs/` 또는 `AGENTS.md`가 존재.
- 이전 `.docs/`가 함께 있지 않음. 있으면 갱신이 아니라 문서 루트 이관·충돌
  절차로 되돌아감.
- 프로젝트 유형(단일/복수)은 Step 2에서 확정.
- 권한 정책이 있으면 SKILL.md의 **선택 권한 정책 연계**에서 현재 계정의 `admin`
  범위와 정확한 갱신 경로를 검증한 상태.

---

## 1. 플러그인 설치 상태 확인

후속 스킬 사용이 실패하면 `harness-kit` 플러그인 설치 상태와 새 세션 여부를 안내한다.
이 스킬은 프로젝트 `.claude/skills/`, `.agents/skills/`, `skills/`에 사용자
스킬을 생성·복사·동기화하지 않는다.

---

## 2. 갱신 계획 사용자 확인

기존 파일과 번들 템플릿을 먼저 읽고 파일별로 다음 상태를 분류한다.

- `new`: 대상 파일이 없음
- `managed`: 정확히 한 쌍의 관리 블록 marker가 있음
- `unmanaged`: marker가 없고 사용자 또는 구버전 내용이 있음
- `malformed`: marker가 중복되거나 시작·끝이 맞지 않음

Markdown marker는
`<!-- harness-kit:managed:start -->` /
`<!-- harness-kit:managed:end -->`, `.gitignore` marker는
`# harness-kit:managed:start` /
`# harness-kit:managed:end`를 사용한다.

각 대상의 현재 내용 hash, 상태, 변경될 관리 블록 diff를 요약하여 사용자에게
확인받는다. `unmanaged` 또는 `malformed` 파일은 자동 갱신 대상에 넣지 않는다.

> ✋ **갱신 대상 확인**
>
> | 유형 | 대상 | 상태 | 처리 |
> |------|------|------|------|
> | `.ai-docs` 안내·정책 | README/.gitignore/_inbox | {new/managed/unmanaged/malformed} | {생성/관리 블록 갱신/보존} |
> | 루트 컨텍스트 | 단일 앱 AGENTS.md 정본 또는 복수 앱 root-context 관리 원본·루트 실행본, CLAUDE.md bridge | {상태} | {처리} |
> | legacy local skill copy | 읽기 전용 report만 출력 |
>
> 진행하시겠습니까? **(승인 / 수정 / 취소)**

---

## 3. `.ai-docs/` 안내·정책 파일 갱신

`.ai-docs/`가 존재하면(단일·복수 공통) 아래 안내·정책 파일의 **관리 블록만**
최신 템플릿으로 맞춘다. 관리 블록 밖의 사용자 확장과 `_inbox/` 내용은
절대 덮어쓰지 않는다.

| 파일 | 단일 앱 템플릿 | 복수 앱 템플릿 | 처리 |
|------|----------------|----------------|------|
| `.ai-docs/README.md` | `docs-readme-single.template` | `docs-readme-multi.template` | 없으면 생성, 있으면 관리 블록만 교체 |
| `.ai-docs/.gitignore` | `docs-gitignore.template` | (동일) | 없으면 생성, 있으면 관리 블록만 교체 |
| `.ai-docs/_inbox/` | — | — | 없으면 생성(`.gitkeep`+README), 내용 보존 |

번들 리소스는 `SKILL.md`의 **플러그인 리소스 해석 계약**으로 읽는다.

1. 프로젝트 유형에 따라 `templates/docs-readme-single.template` 또는
   `templates/docs-readme-multi.template`의 관리 블록을 준비한다.
2. `templates/docs-gitignore.template`의 관리 블록을 준비한다.
3. `.ai-docs/_inbox/`가 없을 때만 디렉토리, 빈 `.gitkeep`,
   `templates/inbox-readme.template` 기반 README를 만든다.
4. 기존 `_inbox/` 내용은 보존한다.

관리 블록 갱신 규칙:

1. `new`면 템플릿 전체를 새 파일로 생성한다.
2. `managed`면 시작 marker부터 끝 marker까지만 새 관리 블록으로 교체하고,
   앞뒤 사용자 내용을 byte-preserve한다.
3. `unmanaged`면 기존 파일과 제안 템플릿의 diff만 보여주고 파일을 보존한다.
   사용자가 명시적으로 마이그레이션을 승인하면 기존 내용을 삭제하지 않고
   관리 블록을 추가하는 merge안을 먼저 사용한다.
4. 사용자가 전체 교체를 별도로 승인한 경우에만 원본을
   `.ai-docs/archive/harness-setup/{timestamp}/{상대경로}`에 백업하고 교체한다.
5. `malformed`면 쓰기를 중단하고 marker 위치와 복구안을 보고한다.
6. 읽은 뒤 승인받기 전 원본 hash와 쓰기 직전 hash가 다르면 동시 수정으로
   판단해 쓰기를 중단하고 diff를 다시 산출한다.

`.ai-docs/`가 아직 없으면 초기 세팅의 해당 단일/복수 구조를 적용해 생성한다.
`AGENTS.md`만 존재한다는 이유로 `.ai-docs/` 생성을 건너뛰지 않는다.

---

## 4. 루트 컨텍스트 갱신

단일 앱은 루트 `AGENTS.md`가 공통 정본이다. 복수 앱은
`.ai-docs/root-context/AGENTS.md`가 Git 관리 원본이고 루트 `AGENTS.md`는 실행본이다.
`CLAUDE.md`는 `@AGENTS.md` bridge와 Claude 전용 차이만 둔다.

단일 앱:
- `AGENTS.md`가 없으면 `templates/root-context-single.template` 기반 뼈대를
  생성한다. `{{APP_ID}}`는 Step 2에서 확정한 단일 앱 식별자로 치환해
  `.ai-docs/{앱}-context.md`를 가리킨다. 기존 파일은 관리 블록만 갱신하고 블록 밖의
  프로젝트 규칙은 보존한다.
- `CLAUDE.md`가 없으면 bridge 템플릿으로 생성한다. 기존 파일은 관리 블록의
  `@AGENTS.md` bridge만 갱신하고 블록 밖 Claude 전용 차이를 보존한다.
- marker가 없는 기존 파일은 Section 3의 `unmanaged` 규칙을 그대로 적용한다.

복수 앱:
- `.ai-docs/root-context/AGENTS.md`의 관리 블록을 검증한 뒤 루트 `AGENTS.md`의 같은
  관리 블록에 반영한다. 루트 실행본을 관리 원본에 자동 역반영하지 않는다.
- 두 위치 모두 없으면 `templates/root-context.template`을 확정된 앱 목록으로
  치환해 양쪽에 생성한다.
- 관리 원본만 없고 루트 실행본만 있으면 자동 승격하지 않는다. 실행본에서 관리 원본을
  복구할 diff를 보여주고 별도 승인을 받은 뒤 생성한다.
- `CLAUDE.md`도 bridge 관리 블록만 동기화하고 각 위치의 블록 밖 Claude 전용
  차이를 보존한다.

---

## 5. 복수 애플리케이션 추가 갱신

프로젝트가 **복수 애플리케이션**인 경우에만 수행.

### 5-1. 루트 컨텍스트 갱신

`.ai-docs/root-context/AGENTS.md`, `.ai-docs/root-context/CLAUDE.md`를 다시 읽어
관리 블록을 검증한 뒤, 루트 파일의 같은 관리 블록에만 반영한다. 파일 전체를
복사하지 않으며 관리 원본과 루트 실행본 각각의 블록 밖 사용자 확장을 보존한다.

> 만약 `.ai-docs/root-context/` 파일이 존재하지 않으면 (다른 스킬에 의해 아직 안 만들어졌거나 삭제된 경우),
> 갱신하지 않고 사용자에게 알린다.

### 5-2. 신규 애플리케이션 감지

Step 2 감지 결과에서 `.ai-docs/{앱}-context.md`가 없는 새 앱 폴더가 발견되면 현재
플랫폼의 파일 도구로 다음을 만든다. 단, 권한 정책이 활성화된 프로젝트에서는
앱 핵심 문서를 `admin`이 대신 만들지 않는다.

- `.ai-docs/{앱}-context.md`
- `.ai-docs/{앱}/context-base/`
- `.ai-docs/{앱}/instruction/`
- `.ai-docs/{앱}/impl-doc/`

사용자에게 신규 앱 추가 사실을 알린다.

권한 정책이 활성화된 경우에는 admin 범위인 루트 컨텍스트와
`.ai-docs/harness/artifact-routing.json`의 앱·repository 지도만 갱신한다.
`.ai-docs/{앱}-context.md`, `context-base/DESIGN.md`, `instruction/*.md`는 만들지 않고,
정책에 새 앱과 `pm-pl` 또는 `app-doc-lead`가 배정돼 있는지 보고한다. 앱 문서 권한자가
`design-doc`과 `context-doc`을 실행할 후속 작업으로 넘긴다. 정책이 없으면 기존 생성
흐름을 유지한다.

---

## 6. legacy local skill copy 읽기 전용 report

`.agents/skills/`, `.claude/skills/` 또는 `skills/*/SKILL.md`가 있으면 다음
기준으로 읽기 전용 분류만 보고한다.

| 분류 | 기준 | 기본 처리 |
|------|------|----------|
| 알려진 옛 하네스 copy | 과거 release inventory와 파일 목록·hash 일치 | 보존, 승인형 migration 후보 |
| 사용자가 수정한 copy | 이름은 같지만 hash 불일치 | 보존, 수동 검토 필요 |
| 무관한 custom skill | 과거 하네스 목록에 없음 | 보존 |
| plugin 이름 충돌 | 현재 plugin 제공 스킬과 같은 이름 | 보존, 충돌 보고 |

승인 전에는 backup·remove·rename을 수행하지 않는다.

---

## 7. 결과 정리

갱신 결과를 요약한다:

```
## 갱신 결과

- `.ai-docs/` 안내·정책: README/.gitignore 관리 블록 갱신됨 / 사용자 확장 보존 / `_inbox/` 유지(또는 신규 생성)
- 루트 컨텍스트: AGENTS 관리 블록 갱신됨 / CLAUDE bridge 갱신됨 / 사용자 확장 보존 / 변경 없음
- (복수앱) 신규 앱 감지: {앱명} (구조 추가됨)
- legacy local skill copy: 읽기 전용 report N건 / 없음
- local skill projection 변경: 없음 (`.agents/skills`, `.claude/skills`, `skills`)
```

## 8. 실행 후 불변조건 검증

이번 실행의 변경 목록이 `.ai-docs/**`, 루트 `AGENTS.md`, 루트 `CLAUDE.md` 안에만
있는지 확인한다. `.agents/skills/**`, `.claude/skills/**`, `skills/**` 변경이
하나라도 있으면 성공으로 보고하지 않는다. 템플릿 placeholder와
`CLAUDE.md` bridge도 함께 검증한다. 갱신 전후 사용자 관리 블록 밖 내용과
legacy local skill copy의 hash가 동일한지 확인하고, backup을 만든 경우 대상
목록과 복구 경로를 결과에 포함한다.

## 9. Portable routing update·manual adoption

`.ai-docs/harness/artifact-routing.json`을 current 상태로 읽고, shared bundle과 각
host-local file을 `created`/`modified`/`unchanged`, `local-only`/`shared`로 나눈
**current/proposed diff**를 먼저 출력한다. root non-Git, `.ai-docs` Git, 각 app Git은
각각 status만 읽어 별도 변경을 보존한다.

`-Plan`/`-Check`은 읽기 전용이고, manual portable adoption의 `-Apply`/`-Uninstall`은
G10 승인 뒤 `-ApproveHostInstall`과 함께만 실행한다. Codex hook은 `/hooks` 신뢰
증적 전까지 `pending-trust`이며 active로 변경하지 않는다.
