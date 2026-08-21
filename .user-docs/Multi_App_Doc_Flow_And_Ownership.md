# 복수 애플리케이션 프로젝트의 AI 문서 흐름과 문서 소유권

> 여러 명이 함께 쓰는 프로젝트에서 `CLAUDE.md` / `AGENTS.md` / `.docs`가 어떤 순서로 만들어지고 어떤 순서로 읽히는지, 그리고 그 문서들을 누가 관리해야 하는지 정리한 문서

## 목차

1. 제1부. 복수 레포 × 복수 애플리케이션
2. 제2부. 문서 소유권 — 누가 무엇을 관리하는가
3. 제3부. 단일 레포 × 복수 애플리케이션

이 문서는 하나의 프로젝트 안에 애플리케이션이 여러 개 있고 그 프로젝트를 여러 사람이 함께 진행할 때를 다룬다. 다루는 범위는 AI 에이전트가 읽는 문서의 흐름과 소유권이다. 애플리케이션 내부의 코드 구조는 다루지 않는다.

설명에 쓰는 예시 프로젝트 이름은 `exam`이고 애플리케이션은 세 개다.

| 애플리케이션 | 성격 |
|---|---|
| `fe-exam-portal` | 포털 프론트엔드 |
| `be-exam-portal` | 포털 백엔드 |
| `be-exam-collector` | 수집 배치 백엔드 |

---

# 제1부. 복수 레포 × 복수 애플리케이션

## 1. 한눈에 보기

### 1.1 스킬 실행 순서

이 복수 레포 구조를 만들고 앱별 설계 기준까지 연결하기 위해 필수로 사용하는 스킬은 아래 네 종류다. 여기서 필수란 플러그인이 네 스킬을 몰래 연속 실행한다는 뜻이 아니다. 각 스킬을 명시적으로 호출하고 필요한 승인을 받아, 네 역할의 산출물이 모두 갖춰져야 이 문서가 전제하는 구조가 완성된다는 뜻이다. `design-doc`과 `context-doc`은 스킬 종류로는 각각 하나지만 대상 앱마다 반복 실행한다.

```text
[이 구조를 성립시키는 필수 스킬 4개]
1. harness-setup            프로젝트·앱 경계와 AI 문서 골격을 만든다.
2. git-scoped-account       프로젝트 하위 앱 레포의 Git 작성자 계정을 맞춘다.
3. design-doc               앱별 설계 기준을 작성한다.
4. context-doc              설계를 AI가 반복해서 읽을 컨텍스트와 지침으로 나눈다.

[네 스킬 이후 — 목적에 맞는 플러그인과 도구를 자유롭게 선택]
기능 구체화                Superpowers brainstorming 등으로 아이디어·요구사항·대안 정리
구현 계획                  impl-doc·impl-fe-be-doc 또는 Superpowers writing-plans 등
프로토타입                 design-prototype-docs·create-prototype 또는 다른 디자인 도구
실제 구현                  frontend-design 또는 Superpowers executing-plans·TDD 등
검증·리뷰                  Superpowers verification-before-completion·requesting-code-review 등

공통 조건                  설계 정본 변경은 design-doc·context-doc으로 반영하고,
                           구현 계획은 앱·사용자별 impl-doc, 코드는 해당 앱 source tree에 저장
```

| 필수 스킬 | 생성·수정하는 핵심 파일 | 이 구조에서 필요한 이유 |
|---|---|---|
| `harness-setup` | 루트 `AGENTS.md`·`CLAUDE.md`, `.docs/README.md`, `.docs/.gitignore`, `.docs/root-context/**`, `.docs/harness/**`, 앱별 빈 문서 디렉토리 | AI가 프로젝트와 앱 경계를 찾고 어떤 문서를 어떤 순서로 읽을지 알 수 있는 공통 지도를 먼저 고정한다 |
| `git-scoped-account` | 컨테이너의 공통 계정 파일(예: `.gitconfig-scoped`)과 각 앱 레포의 `.git/config` 내 `include.path` | 각 앱 레포에 커밋되는 코드와 설정 등 산출물의 Git 이력이 실제 사용자 계정으로 남게 해, 여러 레포에서도 작성자와 변경 출처를 일관되게 추적한다 |
| `design-doc` | `.docs/{앱}/context-base/DESIGN.md` | 도메인·범위·아키텍처·데이터·연동 결정을 앱별 설계 정본으로 만든다. 이 기준이 없으면 이후 지침이 추측으로 채워진다 |
| `context-doc` | `.docs/{앱}-context.md`, `.docs/{앱}/instruction/**`, `.docs/root-context/AGENTS.md`·`CLAUDE.md` 복사본 | 설계 정본을 고정 컨텍스트와 주제별 지침으로 나눠, AI가 대상 앱에 필요한 규칙만 찾아 반복해서 읽게 한다 |

`git-scoped-account`는 산출물 파일의 저장 경로를 정하는 스킬이 아니다. 사용자별 폴더는 `.docs/{앱}/impl-doc/{사용자}/`와 `.docs/prototype/{사용자}/`처럼 라우팅 계약이 나누고, 이 스킬은 앱 레포에 커밋된 산출물의 `user.name`과 `user.email`을 프로젝트 범위에서 일치시킨다. 두 장치를 함께 써야 산출물을 사용자별 위치와 계정별 Git 이력으로 구분할 수 있다. 별도 레포인 `.docs`는 이 스킬의 앱 레포 탐지 대상이 아니므로, 문서 커밋의 계정 출처까지 통일하려면 `.docs` 레포의 로컬 Git 계정도 별도로 확인한다.

네 스킬 이후의 `impl-doc`, `impl-fe-be-doc`, 프로토타입과 실제 구현 스킬은 `harness-kit`을 반드시 써야 하는 단계가 아니다. 다른 플러그인이나 도구로 같은 성격의 산출물을 만들어도 된다. 다만 구현 계획은 `.docs/{앱}/impl-doc/{사용자}/`, 프로토타입은 승인된 prototype 경로, 실제 코드는 해당 앱의 source tree에 두는 산출물 라우팅·소유권 계약은 그대로 지켜야 한다.

### 1.2 최종 구조

위 순서를 모두 마치면 이렇게 된다. 각 줄 오른쪽의 `[관리자]` `[PL]` `[개발자]`는 그 파일을 편집할 수 있는 사람이다. 자세한 기준은 제2부에서 다룬다.

```text
exam/                                          ← 컨테이너 폴더.
│                                                 git init은 하지 않는다.
│
├── AGENTS.md                                  ← [관리자] 세션 시작 때 자동으로 읽는 공통 컨텍스트 정본.
│                                                 AI가 어떤 앱의 문서를 어떤 순서로 읽을지 정하는 탐색 지도다.
├── CLAUDE.md                                  ← [관리자] 첫 줄에서 @AGENTS.md를 참조하는 브리지 파일.
│                                                 내용을 복제하지 않는다.
├── .gitconfig-scoped                          ← [개발자] git-scoped-account가 만든 로컬 공통 계정 설정.
│                                                 앱 레포의 include.path가 이 파일을 참조한다.
│                                                 각 개발자가 자기 작업 환경에서 따로 만들며 공유하지 않는다.
│                                                 파일명은 고정하지 않는다.
│                                                 Gitea를 쓰면 .gitconfig-gitea를 제안한다.
│
├── fe-exam-portal/                            ← [개발자] 프론트엔드 앱 레포.
│                                                 독립 git 레포.
│                                                 실제 소스코드.
├── be-exam-portal/                            ← [개발자] 포털 백엔드 앱 레포.
│                                                 독립 git 레포.
├── be-exam-collector/                         ← [개발자] 외부 데이터 수집 배치 앱 레포.
│                                                 독립 git 레포.
│
└── .docs/                                     ← AI 문서만 관리하는 별도 git 레포.
     │                                        팀 구성원 모두가 clone한다.
     │
     ├── README.md                              ← [관리자] .docs 구조와 스킬별 산출물 위치 안내
     ├── .gitignore                             ← [관리자] _inbox·*.local.* 를 git에서 제외
     │
     ├── _inbox/                                ← 에이전트가 읽을 파일을 잠시 두는 공간.
     │   │                                        스크린샷·로그·표준 문서·외부 산출물 등.
     │   │                                        이곳에 넣은 파일은 git에 올라가지 않는다.
     │   ├── .gitkeep                             폴더 구조를 유지하는 빈 파일
     │   ├── README.md                            _inbox 용도 안내
     │   └── 데이터표준_v1.xlsx                   예: 설계 때 참조할 자료
     │
     ├── .harness/                              ← 점(.)이 붙는 내부 상태 폴더.
     │   │                                        모든 스킬의 실행 로그가 아니라 문서 개선 handoff와 쓰기 승인 상태만 저장한다.
     │   ├── humanize-handoffs.json               어떤 문서에 개선 제안을 이미 했는지 기록한다.
     │   └── artifact-approvals/                  쓰기 1회용 승인 표식이 잠시 머무는 곳이다.
     │
     ├── root-context/                          ← [관리자] 루트 컨텍스트의 원본 복사본.
     │   │                                        갱신할 때 이 사본이 원본 역할을 한다.
     │   ├── AGENTS.md                            담는 것 — 앱 목록·git 경계, 앱별 컨텍스트와 instruction 위치, 산출물 위치 표, 운영 규칙.
     │   │                                        담지 않는 것 — 기술 스택·도메인·코딩 규칙.
     │   │                                        그건 앱별 {앱}-context.md 담당이다.
     │   └── CLAUDE.md                            @AGENTS.md bridge 사본.
     │
     ├── harness/                               ← 점 없는 쪽.
     │   │                                        [관리자]가 관리하는 규칙과 도구다.
     │   │                                        어떤 도구가 만든 산출물이든 설계·컨텍스트·계획·프로토타입·코드 중 무엇인지 식별해 이 구조의 정해진 자리로 보낸다.
     │   ├── README.md                            번들 읽는 순서 안내
     │   ├── artifact-routing.json                앱 id·source_root·docs_root·host 상태 정본
     │   ├── artifact-format-contract.json        산출물 metadata·경로·정규화 규칙
     │   ├── install-routing.ps1                  host hook 설치 계획·확인·승인형 적용
     │   ├── normalize-artifact.ps1               외부 문서를 정본에 반영하기 전 제안 생성
     │   └── hooks/                               Claude·Codex 공용 경로 검사 원본
     │
     ├── fe-exam-portal-context.md              ← [PL] 프론트엔드 앱 고정 컨텍스트.
     │                                            개요·기술 스택·트리·도메인·실행 방법·환경 변수·주의사항 + 지침 인덱스.
     ├── fe-exam-portal/
     │   ├── context-base/
     │   │   └── DESIGN.md                      ← [PL] design-doc 산출물.
     │   │                                        앱 전체 설계 맥락.
     │   ├── instruction/                       ← [PL] 에이전트가 매 작업마다 따르는 규칙.
     │   │   │                                    [항상]은 무조건 생성된다.
     │   │   │                                    [조건]은 설계 문서에 그 주제가 있을 때만.
     │   │   │                                    [추가]는 팀이 요청해서 만든 주제다.
     │   │   ├── agent-instruction.md             [항상] AI 동작 규칙
     │   │   ├── artifact-output-routing-instruction.md  [항상] 산출물 위치·소유권·인계
     │   │   ├── architecture-instruction.md      [조건] 모듈·레이어 경계, 의존성 방향
     │   │   ├── code-style-instruction.md        [조건] 네이밍·예외 처리·주석 스타일
     │   │   ├── framework-instruction.md         [조건] 라이브러리 사용 규칙·금지 패턴
     │   │   ├── api-instruction.md               [조건] API 호출·응답 규약
     │   │   ├── comm-instruction.md              [조건] WebSocket·메시지큐 등 통신 규약
     │   │   ├── file-convention-instruction.md   [조건] 파일 위치·네이밍 규칙
     │   │   └── data-standard-instruction.md     [추가] 용어·도메인·코드 표준
     │   └── impl-doc/                          ← [개발자] 사용자별로 폴더가 갈린다.
     │       └── {사용자}/
     │           ├── 260629-0.fe-exam-portal-roadmap-impl-index.md   ← 로드맵 인덱스 (디렉토리당 1개)
     │           ├── 260629-1.login-form-impl-ui.md                  ← 기능별 구현 계획
     │           └── 260711-1.search-filter-impl-pair.md
     │
     ├── be-exam-portal-context.md              ← [PL] 포털 백엔드 앱 고정 컨텍스트.
     │                                            개요·기술 스택·트리·도메인·실행 방법·환경 변수·주의사항 + 지침 인덱스.
     ├── be-exam-portal/
     │   ├── context-base/
     │   │   └── DESIGN.md                      ← [PL] design-doc 산출물.
     │   │                                        앱 전체 설계 맥락.
     │   ├── instruction/                       ← [PL] [항상] 2개는 같다.
     │   │   │                                    [조건]은 앱마다 다르다.
     │   │   ├── agent-instruction.md             [항상] AI 동작 규칙
     │   │   ├── artifact-output-routing-instruction.md  [항상] 산출물 위치·소유권·인계
     │   │   ├── architecture-instruction.md      [조건] 레이어 경계, 트랜잭션 경계
     │   │   ├── api-instruction.md               [조건] 엔드포인트·요청/응답 스키마
     │   │   ├── framework-instruction.md         [조건] 프레임워크 사용 규칙·금지 패턴
     │   │   ├── egov-springboot-instruction.md   [추가] 표준프레임워크 적용 규칙
     │   │   └── data-standard-instruction.md     [추가] 용어·도메인·코드 표준
     │   └── impl-doc/                          ← [개발자]
     │       └── {사용자}/
     │           ├── 260701-0.be-exam-portal-roadmap-impl-index.md   ← 로드맵 인덱스
     │           ├── 260701-1.user-auth-impl-api.md                  ← 기능별 구현 계획
     │           └── 260705-1.board-crud-impl-api.md
     │
     ├── be-exam-collector-context.md           ← [PL] 수집 배치 앱 고정 컨텍스트.
     │                                            개요·기술 스택·트리·도메인·실행 방법·환경 변수·주의사항 + 지침 인덱스.
     ├── be-exam-collector/
     │   ├── context-base/
     │   │   └── DESIGN.md                      ← [PL] design-doc 산출물.
     │   │                                        앱 전체 설계 맥락.
     │   ├── instruction/                       ← [PL] 이 앱은 API가 없어 api-instruction이 없다.
     │   │   ├── agent-instruction.md             [항상] AI 동작 규칙
     │   │   ├── artifact-output-routing-instruction.md  [항상] 산출물 위치·소유권·인계
     │   │   ├── architecture-instruction.md      [조건] 수집 파이프라인 단계 경계
     │   │   ├── code-style-instruction.md        [조건] 네이밍·예외 처리·주석 스타일
     │   │   ├── framework-instruction.md         [조건] 스케줄러·HTTP 클라이언트 사용 규칙
     │   │   ├── file-convention-instruction.md   [조건] 파일 위치·네이밍 규칙
     │   │   └── data-standard-instruction.md     [추가] 용어·도메인·코드 표준
     │   └── impl-doc/                          ← [개발자]
     │       └── {사용자}/
     │           ├── 260629-0.be-exam-collector-roadmap-impl-index.md ← 로드맵 인덱스
     │           ├── 260629-1.healthcheck-batch-impl-batch.md         ← 기능별 구현 계획
     │           └── 260711-1.news-schema-impl-pipeline.md
     │
     └── prototype/                             ← [개발자] 세 앱이 공유하는 화면 검증용 산출물.
         └── {사용자}/                            예: lhb9397/
             └── {식별자}/                        예: SFR-019/ (요구사항 번호·화면 id)
                 ├── design-doc.md                design-prototype-docs 산출물.
                 │                                        화면 구성·배치 명세
                 ├── index.html                   create-prototype 산출물
                 ├── styles.css
                 ├── app.js
                 └── data/
                     └── mock.json                화면 확인용 더미 데이터
```

편집 권한을 요약하면 이렇다.

| 표기 | 담당 | 대상 |
|---|---|---|
| `[관리자]` | 하네스 세팅 관리자 | 루트 `AGENTS.md`·`CLAUDE.md`, `.docs/README.md`, `.docs/.gitignore`, `.docs/root-context/`, `.docs/harness/` |
| `[PL]` | PL·대리급 개발 리딩 | `{앱}-context.md`, `{앱}/context-base/`, `{앱}/instruction/` |
| `[개발자]` | 각 개발자 | 자기 로컬의 `.gitconfig-scoped`와 앱 레포 Git 계정 설정, `{앱}/impl-doc/{사용자}/`, `prototype/{사용자}/`, 앱 소스 레포 |

Git 계정은 각 개발자가 자기 로컬 컨테이너에서 `git-scoped-account`로 한 번 세팅한다. 이후 그 개발자가 어느 앱 레포에서 커밋하더라도 자기 공통 config 파일에 적힌 계정으로 author가 남는다. 이 파일은 팀이 공유하는 단일 계정 파일이 아니며 컨테이너 루트와 마찬가지로 어떤 git에도 커밋하지 않는다. 개발자마다 자신의 계정 파일을 따로 가지므로 레포별 반복 설정 없이도 산출물의 작성자를 사용자·계정별로 추적할 수 있고, 전역 `~/.gitconfig`도 바뀌지 않는다.

git 경계는 층마다 다르다.

| 대상 | git |
|---|---|
| `exam/` 컨테이너 | git으로 관리하지 않는다 |
| `exam/AGENTS.md`, `exam/CLAUDE.md` | 어떤 레포에도 속하지 않는다. `harness-setup`이 단독 관리한다 |
| `exam/.docs/` | 별도 git 레포. 팀 전체가 clone해서 공유한다 |
| 각 애플리케이션 폴더 | 각자 독립 git 레포 |

### 1.3 에이전트가 문서를 읽는 순서

작업은 항상 컨테이너 루트(`exam/`)에서 세션을 연다는 전제다. 애플리케이션 폴더 안에는 `AGENTS.md`나 `CLAUDE.md`를 두지 않는다. 앱 폴더에서 세션을 열면 루트 컨텍스트가 잡히지 않는다. 앱 레포 안에 컨텍스트를 따로 두면 정본이 둘로 갈라진다.

```text
[세션 시작 — 자동 로드]
  Claude Code  → exam/CLAUDE.md
                  └─ 첫 줄의 @AGENTS.md가 인라인으로 확장되어 함께 로드된다.
  Codex        → exam/AGENTS.md를 그대로 로드한다.

[루트 AGENTS.md의 역할 — AI가 프로젝트를 찾아 읽는 방법을 정하는 안내 지도]
  · 프로젝트 경계             → 컨테이너·앱 3개·.docs의 위치와 git 경계
  · 작업 대상 식별            → 어떤 앱을 대상으로 하는 작업인지 판단하는 기준
  · 앱별 컨텍스트 진입점      → .docs/{앱}-context.md
  · 앱별 세부 규칙 위치        → .docs/{앱}/instruction/
  · 문서를 읽는 순서           → 공통 지도에서 대상 앱의 필요한 주제로 이동
  · 산출물 위치와 라우팅 참조  → .docs/harness/artifact-routing.json
  · 스킬 실행 정책과 운영 규칙

[루트 AGENTS.md에 담지 않는 내용 — 애플리케이션 개발 규칙의 본문]
  · 앱 아키텍처·기술 스택·프레임워크 표준
  · 업무·도메인 맥락과 프로젝트 설계 결정
  · API·데이터·파일·코딩 규칙
  └─ 이런 내용은 .docs/{앱}-context.md와 .docs/{앱}/instruction/에서 읽는다.

[작업 대상 앱을 정한 뒤 — 필요할 때 읽음]
  .docs/{앱}-context.md
      └─ 문서 끝의 "코딩 지침 (Instruction Index)"에서 @ 참조를 따라 읽는다.
         .docs/{앱}/instruction/architecture-instruction.md
         .docs/{앱}/instruction/framework-instruction.md
         .docs/{앱}/instruction/api-instruction.md
         ... 필요한 주제만 읽는다.

[산출물을 만들거나 파일을 쓰기 직전]
  .docs/{앱}/instruction/artifact-output-routing-instruction.md
  .docs/harness/artifact-routing.json
```

여기서 짚어 둘 성질이 있다.

- 자동 로드되는 것은 루트 한 겹뿐이다. 앱별 컨텍스트와 instruction은 루트 문서에 경로로만 적혀 있고 에이전트가 작업 대상을 확정한 뒤에 열어 읽는다. 그래서 루트 `AGENTS.md`는 얇아야 하고 앱이 늘어도 루트가 비대해지지 않는다.
- 새 세션과 서브에이전트는 항상 1번부터 다시 시작한다. 대화 중에 구두로 합의한 내용은 다음 세션에 남지 않는다. 남겨야 하는 규칙은 반드시 앱별 `instruction` 문서에 적어야 다음 세션의 에이전트가 같은 규칙으로 움직인다.

---

## 2. 0단계 — 컨테이너와 레포 준비

스킬을 실행하기 전에 사람이 먼저 해야 하는 준비가 있다.

1. 컨테이너 폴더를 만든다. 예: `D:\Dev_Workspace\exam\`. **이 폴더에는 `git init`을 하지 않는다.**
2. 이번 작업에 필요한 애플리케이션을 컨테이너 바로 아래에 둔다. 기존 레포가 있으면 `git clone`하고 새로 시작하는 앱이면 폴더를 만든다.
3. `.docs`가 이미 팀에 존재하면 그것도 컨테이너 바로 아래에 `git clone`한다. `.docs`는 별도 레포이므로 뒤늦게 합류한 사람은 앱 레포와 `.docs` 레포를 각각 clone해야 같은 문서 맥락을 갖게 된다.

```bash
git clone {앱 레포 주소} fe-exam-portal
```

```bash
git clone {문서 레포 주소} .docs
```

준비가 끝나면 이런 모습이다.

```text
exam/
├── fe-exam-portal/
├── be-exam-portal/
├── be-exam-collector/
└── .docs/          ← 신규 프로젝트라면 아직 없다. harness-setup이 만든다
```

> 애플리케이션을 전부 clone할 필요는 없다. 이번에 볼 앱만 두어도 된다. 다만 그 경우 `harness-setup`이 감지하는 앱 목록도 그만큼만 잡힌다. 앱을 나중에 추가했다면 `harness-setup`을 다시 실행해 루트 컨텍스트를 갱신한다.

---

## 3. `harness-setup`이 맡는 역할

`harness-setup`은 프로젝트에 AI 문서가 놓일 자리와 에이전트가 문서를 읽는 방식을 정한다. 폴더 몇 개를 만드는 초기화 도구에 그치지 않는다. 사람이 관리하는 설계 문서, 에이전트가 읽는 컨텍스트, 여러 도구가 만드는 산출물을 한 구조 안에서 연결하는 문서 하네스다.

이 스킬의 관리 범위는 다음과 같다.

| 관리 대상 | 무엇을 정하는가 | 왜 필요한가 |
|---|---|---|
| `.docs/**` | 설계·컨텍스트·지침·임시 입력·산출물 계약이 놓일 공용 구조 | 문서가 앱 레포와 개인 작업 폴더에 흩어지는 것을 막는다 |
| 루트 `AGENTS.md` | 앱 목록, 문서 위치, 산출물 경로를 가리키는 공통 컨텍스트 정본 | 에이전트가 어느 앱을 작업하든 같은 문서 지도를 읽게 한다 |
| 루트 `CLAUDE.md` | `@AGENTS.md`를 불러오는 bridge와 Claude 전용 차이 | 공통 내용을 복제하지 않고 플랫폼 차이만 분리한다 |
| `.docs/harness/**` | 산출물 위치·형식·소유권·승인·인계에 관한 프로젝트 계약 | 산출물을 만든 플러그인과 관계없이 같은 프로젝트 규칙을 적용한다 |

필수 네 스킬이 담당하는 골격·계정·설계 정본·컨텍스트는 `harness-kit`의 계약으로 만든다. 다른 플러그인의 설계서나 PRD는 `design-doc`이 앱별 `DESIGN.md`를 작성하거나 갱신할 때 쓰는 근거 자료로 받을 수 있지만, 그 파일을 그대로 설계 정본이나 instruction으로 삼지는 않는다. 구현 계획, 프로토타입과 실제 코드 단계부터는 다른 플러그인을 자유롭게 사용할 수 있으며 `.docs/harness/artifact-routing.json`과 앱별 `artifact-output-routing-instruction.md`가 정한 위치와 소유권을 따른다.

외부 플러그인이 만든 파일이 곧바로 정본 위치를 덮어쓰지는 않는다. 출처와 대상이 불분명한 산출물은 `.docs/_inbox/`에서 확인하고 텍스트 문서는 병합 제안과 승인을 거쳐 정본에 반영한다. JSON·YAML·이미지·PDF처럼 손실 없는 자동 변환을 보장하기 어려운 형식은 정본으로 자동 승격하지 않는다.

경로 규칙을 실제 쓰기 단계에서 검사하려면 Claude 또는 Codex용 host adapter가 활성화되어 있어야 한다. 이 가드는 생산자 이름 대신 쓰기 대상 경로를 보기 때문에 다른 플러그인의 로컬 산출물에도 같은 규칙을 적용한다. 기본 세팅만으로 자동 활성화되지는 않으며 사용자의 설치 승인과 신뢰 확인이 필요하다. 동적 shell 경로나 외부 프로세스처럼 로컬 hook이 확실히 판정할 수 없는 작업은 전면 차단하지 않고 우회 증적으로 남긴다.

`harness-setup`은 사용자 스킬을 프로젝트 안에 복사하거나 동기화하지 않는다. `.agents/skills/`, `.claude/skills/`, `skills/`의 사용자 스킬은 설치된 플러그인이 제공하고 이 스킬은 프로젝트 문서 하네스만 관리한다.

---

## 4. 2단계 — `git-scoped-account` (필수·명시 승인)

복수 레포 구조에서 산출물을 사용자·계정별로 추적하기 위해 필요한 스킬이다. 애플리케이션마다 레포가 다르고 사내 Gitea/GitLab 계정과 개인 GitHub 계정이 다른 경우가 많다. 전역 `~/.gitconfig`를 바꾸면 이 프로젝트 밖의 다른 작업까지 영향을 받는다.

이 스킬은 전역 설정을 건드리지 않는다. 컨테이너 폴더에 공통 계정 설정 파일을 하나 만든 뒤 컨테이너 바로 아래 1단계 앱 레포들의 로컬 config에 `include.path`로 그 파일을 참조시킨다. 결과적으로 이 프로젝트 트리 안의 레포에서만 지정한 `user.name` / `user.email`이 적용된다.

공통 config 파일명은 고정값이 아니다. 기본 제안은 `.gitconfig-scoped`이고 호스트나 용도가 뚜렷하면 그에 맞춰 제안한다(사내 Gitea를 쓰면 `.gitconfig-gitea`). 파일 안에는 `user.name`과 `user.email`만 들어간다. 토큰·비밀번호·credential은 넣지 않는다.

```text
Codex        : $git-scoped-account
Claude Code  : /harness-kit:git-scoped-account
```

이 스킬은 명시 호출 전용이다. 일반 git 작업 중에 자동으로 끼어들어 계정을 바꾸지 않는다. 적용 계획을 표로 보여주고 승인받은 뒤에만 파일을 쓴다. 한 레포라도 실패하면 스냅샷으로 전부 되돌린다. 적용이 끝나면 각 앱 레포에서 `git config --show-origin --get user.name`으로 값과 출처를 확인해 보고한다. 이렇게 해야 실제 코드와 앱 레포 안의 산출물 커밋이 다른 계정으로 섞이지 않고 누가 만든 변경인지 Git 이력에서 확인할 수 있다. 별도 `.docs` 레포의 문서·계획·프로토타입은 사용자별 경로로 구분하고, 그 레포의 Git 계정은 별도로 확인한다.

> 중첩된 2단계 이상 레포는 의도적으로 제외한다. 컨테이너 바로 아래에 앱 레포가 없으면 대상 0건으로 종료된다.

### 두 스킬을 마친 뒤의 구조

`harness-setup`과 `git-scoped-account`를 실행하면 패키지 구조가 이렇게 잡힌다. 이 시점에는 골격만 있고 설계·컨텍스트 문서는 아직 비어 있다.

```text
exam/                                     ← 컨테이너 폴더 (git init 하지 않음)
├── AGENTS.md                             ← 공통 AI 컨텍스트 정본
├── CLAUDE.md                             ← @AGENTS.md 를 참조하는 Claude bridge
├── .gitconfig-scoped                     ← git-scoped-account가 만든 공통 계정 설정
│
├── fe-exam-portal/                       ← 프론트엔드 앱 레포 (로컬 config에 include.path 주입됨)
├── be-exam-portal/                       ← 포털 백엔드 앱 레포 (로컬 config에 include.path 주입됨)
├── be-exam-collector/                    ← 수집 배치 앱 레포 (로컬 config에 include.path 주입됨)
│
└── .docs/                                ← 별도 git 레포 (팀 공유용)
    ├── README.md                         ← .docs 구조·산출물 안내
    ├── .gitignore                        ← _inbox 등 로컬 전용 영역 지정
    │
    ├── _inbox/                           ← 에이전트에게 읽힐 파일을 잠시 두는 로컬 전용 공간
    │   ├── .gitkeep
    │   └── README.md
    │
    ├── root-context/                     ← 루트 컨텍스트 원본 복사본 (갱신 시 원본 역할)
    │   ├── AGENTS.md
    │   └── CLAUDE.md
    │
    ├── harness/                          ← 프로젝트 소유 artifact routing bundle
    │   ├── README.md
    │   ├── artifact-routing.json         ← 앱·경로·host 상태 정본
    │   ├── artifact-format-contract.json ← 산출물 metadata·경로·정규화 규칙
    │   ├── install-routing.ps1           ← Plan/Check(읽기 전용) + 승인형 Apply/Uninstall
    │   ├── normalize-artifact.ps1        ← 외부 문서 정본 반영 제안
    │   └── hooks/
    │       ├── artifact-route-core.ps1
    │       ├── approve-artifact.ps1
    │       ├── claude-pre-tool-use.ps1
    │       └── codex-pre-tool-use.ps1
    │
    ├── fe-exam-portal-context.md         ← 프론트엔드 앱 컨텍스트용 빈 파일
    ├── fe-exam-portal/
    │   ├── context-base/                 ← design-doc이 DESIGN.md를 만들 위치
    │   ├── instruction/                  ← context-doc이 지침을 만들 위치
    │   └── impl-doc/                     ← 구현 계획이 쌓일 위치
    │
    ├── be-exam-portal-context.md
    ├── be-exam-portal/
    │   ├── context-base/
    │   ├── instruction/
    │   └── impl-doc/
    │
    ├── be-exam-collector-context.md
    ├── be-exam-collector/
    │   ├── context-base/
    │   ├── instruction/
    │   └── impl-doc/
    │
    └── prototype/                        ← 세 앱이 공유하는 프로토타입 산출물 위치
```

`.docs`를 새로 만든 경우에는 여기서 별도 레포로 초기화하고 원격에 push해야 팀이 공유할 수 있다.

```bash
cd .docs && git init && git add -A && git commit -m "init: 프로젝트 AI 문서 저장소"
```

---

## 5. `design-doc`이 만드는 앱별 설계 기준

`design-doc`은 기능이나 애플리케이션의 요구사항을 개발 판단에 쓸 수 있는 설계 기준으로 정리한다. 결과물인 `DESIGN.md`는 단순한 회의 기록이 아니다. 이 앱이 무엇을 만들고 어디까지 책임지며 어떤 제약을 지켜야 하는지를 한곳에 모은 기준 문서다.

입력 형태는 정해져 있지 않다. 신규 기능은 인터뷰로 요구사항과 범위를 구체화할 수 있고 RFP·SFR·기획서·기존 코드가 있다면 그 자료에서 확정된 사실과 열린 결정을 가려 설계로 정리한다. 어떤 입력을 쓰든 이후 작업에서 다시 해석하지 않아도 되도록 앱의 범위·아키텍처·데이터·인수 기준을 분명히 남긴다.

복수 앱 프로젝트에서는 앱마다 `DESIGN.md`를 따로 둔다.

| 대상 앱 | 설계 기준 문서 |
|---|---|
| `fe-exam-portal` | `.docs/fe-exam-portal/context-base/DESIGN.md` |
| `be-exam-portal` | `.docs/be-exam-portal/context-base/DESIGN.md` |
| `be-exam-collector` | `.docs/be-exam-collector/context-base/DESIGN.md` |

앱별 문서를 분리하는 이유는 프론트엔드, 포털 백엔드, 수집 배치가 서로 다른 도메인과 기술 제약을 갖기 때문이다. 하나의 문서에 모두 섞으면 어떤 규칙이 어느 앱에 적용되는지 모호해진다.

`DESIGN.md`는 `context-doc`, `impl-doc`, `impl-fe-be-doc` 같은 후속 작업의 공통 입력으로 쓰인다. 설계 기준이 바뀌면 `design-doc`으로 같은 문서를 갱신하고 저장 위치와 소유권은 해당 앱의 `artifact-output-routing-instruction.md`를 따른다. 다른 플러그인이 만든 기획서나 설계서는 근거 자료로 사용할 수 있지만, 그 파일을 그대로 정본으로 삼지 않고 `design-doc`의 검토·승인 과정을 거쳐 `DESIGN.md`에 반영한다.

---

## 6. `context-doc`이 만드는 컨텍스트와 지침

`context-doc`은 앱별 `DESIGN.md`에서 에이전트가 반복해서 읽어야 할 사실과 규칙을 꺼내 **애플리케이션 컨텍스트**와 주제별 instruction으로 나눈다. 여기서 컨텍스트는 해당 애플리케이션의 업무·도메인 맥락, 설계 원칙, 아키텍처 개요, 기술 스택, 실행 방법과 반복 적용 규칙을 뜻한다. 하네스가 문서 위치와 읽는 순서만 안내하는 루트 컨텍스트와는 역할이 다르다.

### 6.1 무엇을 만들고 왜 나누는가

| 산출물 | 위치 | 역할 |
|---|---|---|
| 애플리케이션 컨텍스트 | `.docs/{앱}-context.md` | 해당 앱의 업무·도메인 맥락, 설계 원칙, 아키텍처 개요, 기술 스택, 주요 구조, 실행·검증 방법과 지침 인덱스를 담는다 |
| 앱별 지침 | `.docs/{앱}/instruction/*-instruction.md` | 아키텍처·API·프레임워크처럼 작업 중 필요한 규칙을 주제별로 분리한다 |
| 하네스 루트 컨텍스트 복사본 | `.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md` | 앱 목록, git 경계, 애플리케이션 컨텍스트·지침의 위치와 읽는 순서를 루트 문서에 반영할 원본 역할을 한다. 앱의 설계·기술 규칙 본문은 담지 않는다 |

두 파일 모두 이름에 "컨텍스트"가 들어가지만 답하는 질문이 다르다.

- **애플리케이션 컨텍스트**는 "이 앱은 무엇을 만들며 어떤 설계·기술 원칙으로 동작하는가?"에 답한다. PL·개발 리딩이 관리하며 실제 앱 작업의 배경지식이 된다.
- **하네스 루트 컨텍스트**는 "현재 프로젝트에 어떤 앱이 있고, AI가 대상 앱의 컨텍스트와 지침을 어디서 어떤 순서로 읽어야 하는가?"에 답한다. 하네스 세팅 관리자가 관리하는 탐색 지도다.

애플리케이션 컨텍스트는 앱의 고정 사실과 지침의 위치를 알려주는 얇은 문서로 유지하되, 단순한 경로 목록으로 축소하지 않는다. 앱의 설계·기술 맥락을 이해하는 데 필요한 핵심 내용은 담고 세부 규칙만 instruction으로 분리한다. 그러면 에이전트가 작업과 관계없는 규칙까지 매번 읽지 않아도 되고 같은 규칙이 여러 문서에 복제되는 문제도 줄어든다.

`context-doc`은 복수 앱 프로젝트의 루트 `AGENTS.md`와 `CLAUDE.md`를 직접 덮어쓰지 않는다. 애플리케이션 컨텍스트와 instruction을 만든 뒤 `.docs/root-context/`의 하네스 지도 복사본에 그 위치와 참조만 갱신한다. 실제 루트 파일 반영은 문서 하네스의 소유자인 `harness-setup`이 맡는다. 이 경계를 두면 앱의 설계·기술 맥락을 관리하는 사람과 전체 문서 배선을 관리하는 사람의 책임이 섞이지 않는다.

### 6.2 어떤 instruction을 만드는가

`agent-instruction.md`와 `artifact-output-routing-instruction.md`는 모든 앱에 필요하다. 나머지 파일은 설계 문서에 해당 규칙이 있을 때만 만든다.

| 파일 | 담는 내용 |
|---|---|
| `agent-instruction.md` | AI가 사람과 다르게 처리해야 할 행동 규칙 |
| `artifact-output-routing-instruction.md` | 산출물의 위치·소유권·승인·인계 기준 |
| `architecture-instruction.md` | 모듈·레이어 경계와 의존성 방향 |
| `code-style-instruction.md` | 네이밍·예외 처리·주석 스타일 |
| `framework-instruction.md` | 라이브러리 사용 규칙과 금지 패턴 |
| `api-instruction.md` | API 엔드포인트와 요청·응답 규약 |
| `comm-instruction.md` | WebSocket·메시지큐 등 통신 규약 |
| `file-convention-instruction.md` | 파일 위치와 네이밍 규칙 |

팀 고유의 데이터 표준, 보안 규약, 전자정부 프레임워크 규칙도 같은 방식으로 분리할 수 있다. 근거가 `DESIGN.md`나 팀 표준 문서에 있어야 하며 근거가 없는 빈 instruction이나 추측으로 만든 규칙은 남기지 않는다.

### 6.3 다른 플러그인의 산출물과 연결되는 방식

`artifact-output-routing-instruction.md`는 어떤 스킬이 파일을 만들었는지가 아니라 그 산출물이 무엇이며 어느 앱에 속하는지를 기준으로 저장 위치를 정한다. 따라서 다른 플러그인이 만든 구현 계획, 프로토타입, 보고서도 플러그인의 기본 경로보다 프로젝트의 산출물 계약을 우선한다.

`context-doc`은 이 계약을 앱별 instruction으로 문서화하고 `harness-setup`은 프로젝트 공용 routing bundle과 선택적으로 활성화한 host guard를 통해 계약을 연결한다. 외부 산출물을 정본으로 옮길 때는 `.docs/_inbox/`에서 출처와 형식을 확인하고 승인된 항목만 반영한다. 그래서 도구가 달라져도 문서의 위치와 소유권은 바뀌지 않는다.

### 6.4 결과로 정리되는 `.docs`

```text
.docs/
├── README.md
├── .gitignore
├── _inbox/
├── .harness/                             ← 문서 개선·쓰기 승인 내부 상태 (사람이 편집 안 함)
│   └── humanize-handoffs.json            ← 문서 개선 제안 이력
├── root-context/                         ← 하네스 탐색 지도 복사본. 앱 설계·기술 규칙 본문은 담지 않음
│   ├── AGENTS.md                         ← context-doc이 참조 위치 갱신, harness-setup이 루트에 반영
│   └── CLAUDE.md
├── harness/
│   └── ...
│
├── fe-exam-portal-context.md             ← 애플리케이션 컨텍스트 (설계·원칙·기술 스택·지침 인덱스)
├── fe-exam-portal/
│   ├── context-base/
│   │   └── DESIGN.md                     ← design-doc 산출물
│   ├── instruction/
│   │   ├── agent-instruction.md
│   │   ├── artifact-output-routing-instruction.md
│   │   ├── architecture-instruction.md
│   │   ├── framework-instruction.md
│   │   ├── api-instruction.md
│   │   ├── file-convention-instruction.md
│   │   └── data-standard-instruction.md  ← 팀이 필요해서 추가한 주제
│   └── impl-doc/
│
├── be-exam-portal-context.md
├── be-exam-portal/
│   ├── context-base/DESIGN.md
│   ├── instruction/
│   │   ├── agent-instruction.md
│   │   ├── artifact-output-routing-instruction.md
│   │   ├── api-instruction.md
│   │   ├── egov-springboot-instruction.md
│   │   └── data-standard-instruction.md
│   └── impl-doc/
│
├── be-exam-collector-context.md
├── be-exam-collector/
│   ├── context-base/DESIGN.md
│   ├── instruction/
│   │   ├── agent-instruction.md
│   │   ├── artifact-output-routing-instruction.md
│   │   ├── architecture-instruction.md
│   │   ├── code-style-instruction.md
│   │   ├── framework-instruction.md
│   │   ├── file-convention-instruction.md
│   │   └── data-standard-instruction.md
│   └── impl-doc/
│
└── prototype/
```

앱마다 instruction 목록이 다른 것이 정상이다. 프론트에는 아키텍처·프레임워크 규칙이 두껍게 붙고 백엔드에서는 API·프레임워크 규약이 늘어난다. 공통으로 지켜야 할 표준(예: 데이터 표준)만 세 앱에 같은 이름으로 들어간다.

---

## 7. `.docs/harness/`는 무엇을 고정하는가

`.docs/harness/`는 `harness-setup`이 만드는 프로젝트 소유(project-owned) 산출물 라우팅 번들이다. 여기 담긴 계약은 이런 것이다. 특정 플러그인이나 도구가 사라져도 이 폴더만 읽으면 "무엇을 어디에 쓰고, 누가 그 산출물의 주인이며, 어떤 승인이 필요한지"를 확인할 수 있다.

이 번들은 `harness-kit`의 후속 스킬만을 위한 설정이 아니다. 최초의 `harness-setup`으로 이 계약을 만든 뒤에는 Superpowers 같은 다른 플러그인의 스킬이나 일반 코딩 도구를 사용해도 같은 규칙을 적용한다. producer 이름을 보고 경로를 정하지 않고, 산출물이 **설계·컨텍스트·구현 계획·프로토타입·디자인 시스템·실제 코드 중 무엇인지**, 어느 앱의 작업인지, 누가 소유하는지를 판정해 프로젝트의 정본 위치로 보낸다.

예를 들어 Superpowers를 사용해도 별도의 `docs/superpowers/` 문서 트리를 정본으로 만들지 않는다.

| 외부 스킬의 산출물 | 판정하는 계열 | 이 프로젝트에서의 처리 |
|---|---|---|
| Superpowers `brainstorming`이 만든 요구사항·설계 초안 | 설계 입력 | `.docs/_inbox/`에서 확인한 뒤 `design-doc`을 통해 `.docs/{앱}/context-base/DESIGN.md`에 반영 |
| Superpowers `writing-plans`가 만든 작업 계획 | 구현 계획 | `.docs/{앱}/impl-doc/{사용자}/`에 저장 |
| Superpowers `executing-plans`가 만든 코드와 테스트 | 실제 코드 | 해당 앱의 source tree에만 저장하고 다른 앱 경계를 넘지 않음 |
| 다른 디자인 플러그인이 만든 화면 시안 | 프로토타입 | 승인된 `.docs/prototype/{사용자}/{식별자}/`에 저장 |

이 계약을 사람이 읽는 상세 진입점은 앱별 `.docs/{앱}/instruction/artifact-output-routing-instruction.md`다. `context-doc`이 이 instruction을 항상 만들며, 그 안에서 `.docs/harness/artifact-routing.json`과 `.docs/harness/artifact-format-contract.json`을 함께 읽도록 지시한다. `artifact-routing.json`은 앱·소유권·정본 경로와 host 상태를 제공하고, `artifact-format-contract.json`은 산출물 종류·필수 metadata·경로 형식을 제공한다. 루트 `AGENTS.md`는 산출물을 만들기 전에 대상 앱의 이 instruction으로 이동하도록 안내하는 지도 역할만 한다.

강제력은 두 단계다. instruction과 루트 문서는 어떤 에이전트나 플러그인이든 따라야 하는 프로젝트 계약이다. Claude·Codex용 host routing hook까지 사용자가 승인하고 `active`로 전환한 경우에는 실제 파일 쓰기 직전에 대상 경로를 검사해, Superpowers의 기본 `docs/superpowers/specs/`·`docs/superpowers/plans/`처럼 계약 밖 경로를 거부하고 앱별 routing instruction을 안내한다. hook이 활성화되지 않았다면 문서 계약은 유효하지만 파일 쓰기를 물리적으로 차단하지는 않는다.

### 먼저 — `.harness/`와 `harness/`는 다른 것이다

`.docs` 아래에 이름이 거의 같은 폴더가 둘 있다. 점 하나 차이지만 성격이 정반대다.

| | `.docs/harness/` (점 없음) | `.docs/.harness/` (점 있음) |
|---|---|---|
| 무엇인가 | 규칙과 도구 | 문서 개선·쓰기 승인의 내부 상태 |
| 담긴 것 | 경로 계약(`artifact-routing.json`), 형식 계약, 설치·정규화 스크립트, hook 원본 | 개선 제안 이력(`humanize-handoffs.json`), 일회용 쓰기 승인 표식 |
| 누가 만드나 | `harness-setup`이 세팅할 때 | 최외곽 문서 producer가 첫 handoff를 기록하거나 승인 스크립트가 표식을 만들 때 |
| 누가 편집하나 | 하네스 세팅 관리자 | 관련 스킬과 hook이 자동 갱신한다. 사람이 직접 편집하지 않는다 |
| 읽을 일이 있나 | 있다. 산출물 위치가 헷갈릴 때 사람이 확인한다 | 관련 스킬과 hook이 읽는다. 사람은 보통 확인하지 않는다 |
| 지우면 | 경로 계약이 사라진다. 다시 세팅해야 한다 | 기록이 초기화된다. 이미 넘어간 제안이 다시 올라올 수 있다 |

한 줄로 줄이면 이렇다. `harness/`는 **무엇을 어디에 써야 하는가**를 정하고, `.harness/`는 **무엇을 이미 했는가**를 기억한다.

`.harness/humanize-handoffs.json`이 하는 일이 그 예다. 문서를 다듬자는 제안을 한 번 하고 사용자가 적용·건너뛰기·거절을 결정하면 그 상태를 여기에 남긴다. 최종 Markdown의 경로와 내용 hash로 fingerprint를 만들기 때문에, 같은 문서 묶음이 바뀌지 않았다면 다음 사람의 새 세션에서도 같은 제안을 반복하지 않는다.

이 ledger를 직접 사용하는 스킬은 현재 다음과 같다.

| 최외곽 문서 producer | ledger에 기록하는 대상 |
|---|---|
| `harness-setup` | 세팅 과정에서 만든 Markdown 문서 묶음의 개선 handoff |
| `harness-bootstrap` | bootstrap 전체 산출물 묶음의 개선 handoff |
| `design-doc` | 앱별 설계 문서 묶음의 개선 handoff |
| `context-doc` | 앱 컨텍스트와 instruction 문서 묶음의 개선 handoff |
| `impl-doc` | 단일 영역 구현 계획서와 로드맵 인덱스의 개선 handoff |
| `impl-fe-be-doc` | FE·API·BE·DB 통합 구현 계획서와 인덱스의 개선 handoff |
| `design-prototype-docs` | 화면 설계 문서 묶음의 개선 handoff |

여기서 **최외곽 문서 producer**는 이번 작업의 최종 산출물을 책임지는 스킬을 뜻한다. 예를 들어 `harness-bootstrap`이 내부에서 `design-doc`과 `context-doc`을 호출하면 두 하위 스킬은 각자 윤문을 제안하지 않는다. `harness-bootstrap`이 전체 문서 묶음에 대해 한 번만 제안하고 ledger도 한 번만 갱신한다. 반대로 `design-doc`을 직접 호출했다면 `design-doc`이 producer가 된다.

실제 문장 다듬기는 `harness-kit:humanize-korean`이 수행하지만, fingerprint 계산과 `proposed`, `skipped`, `rejected`, `applied`, `revalidated` 상태 기록은 최외곽 producer가 책임진다. 따라서 `humanize-korean`이 `.harness/` 전체를 관리하는 구조가 아니다. 다른 플러그인의 `humanize-korean:humanize`를 사용자가 별도로 호출한 경우도 최외곽 producer의 handoff 계약을 통하지 않았다면 이 ledger에 자동 기록되지 않는다.

`motion-design`과 `ui-ux-pro-max`에도 최외곽 producer일 때 윤문을 제안한다는 규칙은 있다. 다만 현재 스킬 원문에는 `humanize-handoffs.json`을 직접 갱신하는 계약이 명시돼 있지 않다. 그러므로 위 표의 ledger 직접 적용 스킬과는 구분한다.

`.harness/artifact-approvals/`는 윤문 이력이 아니다. `harness-setup`이 설치한 3층 경로 검사 hook이 활성화됐을 때, 보호된 산출물 경로에 한 번 쓸 수 있도록 승인 스크립트가 만든 표식을 잠시 보관한다. 이 표식은 한 번 쓰이면 소모되고 시간이 지나면 만료된다. 특정 문서 작성 스킬 하나에 귀속되는 것이 아니라, 활성화된 hook을 통과해 보호 경로에 쓰려는 모든 도구와 플러그인에 적용된다.

### 번들이 동작하는 층

번들은 층을 나눠 동작한다.

| 층 | 대상 | 강제력 |
|---|---|---|
| 1층 | 루트 `AGENTS.md` / `CLAUDE.md`의 참조 | 에이전트가 문서를 읽고 따르는 수준 |
| 2층 | 앱별 `artifact-output-routing-instruction.md` | 에이전트가 문서를 읽고 따르는 수준 |
| 3층 | host별 write hook (`.claude/`, `.codex/`) | 실제 쓰기 시점의 경로 검사 |

관련 instruction은 앱별 `artifact-output-routing-instruction.md`다. 이 파일이 산출물 종류별 정본 위치의 상세 기준이며 `context-doc`이 주제 유무와 관계없이 항상 만든다. 여기에 적히는 항목은 이렇다.

- 산출물 종류별 정본 경로 (설계·컨텍스트·구현 계획·프로토타입·design system·실제 코드)
- 산출물의 owner와 인계 규칙
- 덮어쓰기·이동·삭제에 필요한 승인 절차
- 금지 사항: 앱 A에서 앱 B의 경로에 쓰지 않는다, `.docs` 밖에 쓰지 않는다, 프로토타입 코드를 제품 소스로 복사하지 않는다

`.docs/harness/artifact-routing.json`은 기계 판독용 정본이다. 여기에는 앱 식별자, `source_root`, `docs_root`, `prototype_owner`, 앱별 컨텍스트 경로와 host 상태가 들어간다. 여기서 프로젝트 단위 예외도 확정된다. 예를 들어 프로토타입은 스킬의 기본값이 앱별 디렉토리다. `exam` 프로젝트처럼 세 앱이 하나의 `.docs/prototype/`을 공유하기로 했다면 `prototype_owner`와 라우팅 instruction의 프로젝트 적용 절이 우선한다.

### 다른 플러그인의 산출물을 이 구조로 끌어오는 방식

이 번들은 **산출물을 도구 이름이 아니라 성격으로 분류한다.** 다만 모든 계열에서 producer 선택이 자유로운 것은 아니다. 설계 정본은 `design-doc`, 컨텍스트와 instruction은 `context-doc`이 책임진다. 다른 플러그인이 만든 설계서·PRD·규칙 초안은 `_inbox`에서 확인한 뒤 이 두 필수 스킬의 입력 근거로 사용한다. 구현 계획, 프로토타입과 실제 코드부터는 producer를 자유롭게 선택하고 산출물의 성격에 맞는 정본 위치로 보낸다.

| 산출물 계열 | producer 기준 | 정본 위치 |
|---|---|---|
| 설계·요구사항 | `design-doc` 필수. 외부 설계서·PRD는 입력 근거로만 사용 | `.docs/{앱}/context-base/DESIGN.md` |
| 컨텍스트·규칙 | `context-doc` 필수. 설계 정본을 근거로 생성 | `.docs/{앱}-context.md`, `.docs/{앱}/instruction/` |
| 구현 계획 | producer 자유. 작업 계획서·Phase 계획·체크리스트·로드맵 포함 | `.docs/{앱}/impl-doc/{사용자}/` |
| 프로토타입 | producer 자유. 화면 시안·wireframe·검증용 HTML 포함 | `.docs/prototype/{사용자}/{식별자}/` |
| 디자인 시스템 | producer 자유. 저장이 승인된 경우만 정본 반영 | `.docs/{앱}/design-system/{project-slug}/` |
| 실제 코드 | 구현 플러그인·코딩 도구·사람의 직접 작업 모두 허용 | 해당 앱의 source tree |
| 미분류·외부 반입 | 스크린샷·로그·외부 문서·분류가 서지 않는 것 | `.docs/_inbox/` (git 미추적) |

그래서 다른 플러그인의 계획 스킬이 만든 문서라도 최종 위치는 `.docs/{앱}/impl-doc/{사용자}/`다. 다른 디자인 플러그인이 뽑은 화면 시안도 `.docs/prototype/{사용자}/{식별자}/`다. 도구가 자기 관례대로 `docs/`, `plans/`, `.notes/`나 앱 소스 트리 안에 파일을 만들려 하면 그것은 계약 위반으로 본다.

강제되는 지점은 세 곳이다.

1. **쓰기 전 판정.** 에이전트는 파일을 만들기 전에 앱별 `artifact-output-routing-instruction.md`와 `artifact-routing.json`을 읽고 대상 앱과 계열을 확정한다. 둘 중 하나라도 모호하면 파일을 만들지 않고 사람에게 확인한다.
2. **경로 검사.** 3층 hook이 `active`이면 쓰기 시점에 경로가 계약 안에 있는지 검사한다. 기존 정본 파일, 승인된 앱 소스, `.docs/_inbox/**`는 통과하고, 새 관리 문서는 경로·내용 해시에 묶인 일회용 승인 표식이 있어야 통과한다.
3. **정본 반영 승인.** `_inbox`에 들어온 외부 산출물은 `normalize-artifact.ps1 -Plan`으로 어느 정본에 어떻게 병합될지 제안을 먼저 만들고, 승인 뒤에만 반영된다.

같은 계열의 산출물이 서로 다른 위치에 흩어지면 두 가지가 깨진다. 다음 세션의 에이전트가 계획서를 찾지 못하고, 로드맵 인덱스가 사람마다 따로 생긴다. 계열 분류를 강제하는 이유가 이것이다.

### host hook의 실제 강제 범위

3층은 자동으로 켜지지 않는다.

| 상태 | 뜻 |
|---|---|
| `not-installed` | host 설정과 adapter 파일이 없다. 기계적 write hook은 동작하지 않는다 |
| `pending-trust` | 공유 번들은 준비됐지만 host 신뢰 절차가 끝나지 않았다. 활성 보호 장치로 보지 않는다 |
| `active` | 관리자가 host별 hook 검토를 마치고 신뢰 증적을 승인했다 |
| `uninstalled` | 승인된 절차로 해제했다 |

설치는 `install-routing.ps1 -Plan`(읽기 전용)으로 변경 제안을 먼저 확인하고 별도 승인과 함께 `-Apply -ApproveHostInstall`을 실행해야 진행된다. 설치 직후에도 상태는 `pending-trust`다. host의 hook 검토 증적을 제시한 뒤 `-ActivateTrust -ApproveTrustEvidence`를 실행해야 `active`가 된다.

이 hook은 보안 sandbox가 아니다. 동적 shell 대상, 명령 실행 후의 redirect, host가 제공하는 도구, 프로젝트 밖 프로세스는 완전히 판정할 수 없어 "우회 증적"으로 기록될 뿐이다. **실질적인 강제력의 대부분은 1·2층, 즉 문서 계약에서 나온다.** 그래서 뒤에 나올 문서 소유권 분리가 중요해진다.

---

## 8. 개발자별 산출물은 어디에 생기는가

세팅과 컨텍스트가 끝나면 그 뒤는 개발자 각자의 반복 작업이다. 이때부터는 아래 `harness-kit` 스킬을 사용해도 되고, 다른 플러그인이나 도구로 산출물을 만들어도 된다. 이 표의 스킬 이름은 필수 도구가 아니라 해당 산출물을 만드는 대표 예시다. 어떤 도구를 사용하든 산출물은 사용자 식별자로 나뉜 정본 경로에 저장한다. 여러 명이 같은 `.docs` 레포를 공유해도 서로의 작업 문서가 섞이지 않게 하기 위해서다.

| 대표 producer | 산출물 위치 |
|---|---|
| `impl-doc` | `.docs/{앱}/impl-doc/{사용자}/{YYMMDD}-{순번}.{기능}-impl-{종류}.md` |
| `impl-fe-be-doc` | 같은 규칙. 같은 디렉토리에 섞이며 작성 스킬은 문서 머리말의 `생성 스킬:` 표기로 구분한다 |
| 로드맵 인덱스 | `.docs/{앱}/impl-doc/{사용자}/{YYMMDD}-0.{앱이름}-roadmap-impl-index.md` (디렉토리당 1개) |
| `design-prototype-docs` | `.docs/prototype/{사용자}/{식별자}/design-doc.md` |
| `create-prototype` | `.docs/prototype/{사용자}/{식별자}/` 아래 HTML/CSS/JS |

예시:

```text
.docs/be-exam-collector/impl-doc/lhb9397/
├── 260629-0.be-exam-collector-roadmap-impl-index.md   ← 로드맵 인덱스 (순번 0 고정)
├── 260629-1.healthcheck-batch-impl-batch.md
├── 260711-1.collector-news-schema-impl-pipeline.md
└── design-roadmap/
    ├── 260629-0.collector-roadmap-impl-index.md
    └── 260724-1.collector-overview.md

.docs/prototype/lhb9397/SFR-019/
├── index.html
└── ...
```

`impl-reuse-scan`, `impl-verify`, `doc-audit`, `multi-review`처럼 점검 성격의 스킬은 기본이 보고 전용이다. 명시적으로 저장을 요청하지 않으면 파일을 만들지 않고 대화창에만 결과를 낸다.

### 다른 플러그인의 비슷한 스킬을 썼을 때

여기가 실제로 자주 어긋나는 지점이다. 개발자마다 설치한 플러그인이 다르고 다른 플러그인의 계획·리뷰·문서 생성 스킬은 이 프로젝트의 `.docs` 규약을 알지 못한다. 그런 스킬은 대개 아래 위치에 파일을 만든다.

- 현재 작업 디렉토리 루트 (`exam/` 또는 앱 레포 루트)
- 그 플러그인이 정한 자체 폴더 (`docs/`, `plans/`, `.notes/` 등)
- 앱 소스 트리 안쪽

이 결과물은 `.docs`에도 없고 앱 레포 커밋 대상에도 애매하게 걸린다. 앱 레포에 들어가면 소스 리뷰에 문서 노이즈가 섞인다. 컨테이너 루트에 남으면 어떤 git에도 속하지 않아 그 사람 로컬에서만 존재하다 사라진다.

운영 기준은 이렇게 잡는다.

1. **먼저 `.docs/_inbox/`로 받는다.** 외부 스킬이나 외부에서 받은 문서는 일단 `_inbox`에 둔다. 이 폴더는 `.docs/.gitignore`가 내용을 제외하므로 커밋되지 않는다.
2. **정본으로 올릴 때만 옮긴다.** `.docs/harness/normalize-artifact.ps1 -Plan`으로 어떤 정본 파일에 어떻게 병합될지 제안을 먼저 보고 승인 뒤 `-Promote -ApprovePromotion`으로 반영한다. Markdown 계열 텍스트만 이 경로를 탄다. JSON/YAML·이미지·PDF는 손실 없는 변환을 보장할 수 없어 `_inbox` 매니페스트에만 기록한다.
3. **같은 성격의 산출물은 위치를 통일한다.** 구현 계획 문서를 다른 플러그인으로 만들었더라도 최종 위치는 `.docs/{앱}/impl-doc/{사용자}/`다. 위치가 갈리면 다음 세션의 에이전트가 계획서를 찾지 못하고 로드맵 인덱스도 두 벌이 된다.
4. **판단이 서지 않으면 만들지 않는다.** 라우팅 instruction은 대상 앱이나 경로가 모호하면 파일을 만들거나 옮기지 말고 사람에게 먼저 확인하도록 정한다.

---

# 제2부. 문서 소유권 — 누가 무엇을 관리하는가

여기까지가 구조와 흐름이다. 이 문서의 핵심은 그다음이다. `.docs` 안의 문서는 성격이 서로 다르고 다른 사람이 관리해야 한다.

## 9. 세 종류의 문서

`.docs` 아래 파일은 겉보기에 전부 Markdown이다. 실제로는 소유권과 쓰임에 따라 세 종류로 나뉜다.

**(A) AI가 문서를 읽는 흐름을 정하는 문서.** 루트 `AGENTS.md`, 루트 `CLAUDE.md`, `.docs/root-context/`의 복사본, `.docs/README.md`, `.docs/.gitignore`, `.docs/harness/**`가 여기 속한다. 이 파일들의 내용은 개발 지식이 아니다. "어떤 앱이 있고, 앱별 컨텍스트가 어디 있으며, 산출물을 어디에 쓰고, 무엇을 자동 로드하고 무엇을 참조로 남길지"를 정한다. 즉 하네스의 배선도다.

**(B) 팀이 함께 따르는 설계·규칙 문서.** 앱별 `DESIGN.md`, `{앱}-context.md`, `{앱}/instruction/*.md`가 여기 속한다. 도메인, 아키텍처, 기술 스택, API 규약, 코딩 규칙처럼 앱 전체에 영향을 주는 기준을 담는다. 해당 앱을 이해하고 팀의 결정을 책임지는 PL·대리급 개발 리딩이 관리한다.

**(C) 개발자가 자기 작업을 계획하고 추적하는 문서.** 앱별 `.docs/{앱}/impl-doc/{사용자}/**`와 `.docs/prototype/{사용자}/**`가 여기 속한다. 기능별 구현 계획, 작업 순서, 검증 기준, 진행 상태와 임시 검증 산출물을 담는다. 앱과 사용자 단위로 분리하며 해당 개발자가 직접 관리한다.

세 종류를 같은 사람이 같은 기준으로 고치면 문제가 생긴다. (A)를 개발자가 편의로 고치면 자동 로드 순서와 경로 계약이 조용히 깨진다. 그 결과는 "에이전트가 갑자기 규칙을 안 지킨다"는 형태로 며칠 뒤에 나타난다. (B)를 하네스 관리자가 대신 쓰면 실제 도메인과 다른 규칙이 고정 맥락으로 박힌다. 반대로 (C)를 리딩이나 관리자가 대신 관리하면 실제 구현을 맡은 개발자의 판단과 진행 상태가 문서에서 빠진다.

`.docs/.harness/**`는 이 세 종류에 포함하지 않는다. 사람에게 지식을 전달하는 문서가 아니라 관련 스킬과 hook이 읽고 쓰는 내부 상태이기 때문이다. 상태 파일의 형식과 동작 규칙은 하네스 세팅 관리 영역이지만, 실제 값은 최외곽 문서 producer와 쓰기 보호 hook이 자동 갱신한다. PL이나 개발자가 내용을 직접 관리하지 않는다.

## 10. 소유권 분리

| 계층 | 대상 경로 | 소유자 | 근거 |
|---|---|---|---|
| 배선 | 루트 `AGENTS.md`, 루트 `CLAUDE.md` | 하네스 세팅 관리자 | 자동 로드 진입점. 여기가 깨지면 전체 문서 흐름이 멈춘다 |
| 배선 | `.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md` | 하네스 세팅 관리자 | 루트 파일의 원본. 갱신은 `harness-setup` 재실행으로만 |
| 배선 | `.docs/README.md`, `.docs/.gitignore` | 하네스 세팅 관리자 | `.docs` 구조·추적 정책의 정본 |
| 배선 | `.docs/harness/**` | 하네스 세팅 관리자 | 경로·형식·host 설치 상태 계약. 승인 절차 자체를 정의한다 |
| 상태 | `.docs/.harness/**` | 관련 producer·hook 자동 관리 | 문서 개선 handoff와 일회용 쓰기 승인 상태. 사람이 직접 편집하지 않는다 |
| 로컬 계정 | 컨테이너의 `.gitconfig-scoped` 계열 파일과 앱 레포의 `.git/config` 참조 | 각 개발자 | 자기 작업 환경의 산출물 커밋을 자신의 Git 계정으로 남긴다. 팀과 파일을 공유하지 않는다 |
| 설계 | `.docs/{앱}/context-base/**` | PL·대리급 개발 리딩 | 앱 전체 설계 맥락. 이후 모든 산출물의 입력 |
| 설계 | `.docs/{앱}-context.md` | PL·대리급 개발 리딩 | 앱 고정 맥락과 지침 인덱스 |
| 설계 | `.docs/{앱}/instruction/**` | PL·대리급 개발 리딩 | 팀 전체에 반복 적용되는 규칙 |
| 작업 | `.docs/{앱}/impl-doc/{사용자}/**` | 해당 개발자 | 기능별 구현 계획과 로드맵 인덱스. 앱과 사용자별로 분리한다 |
| 작업 | `.docs/prototype/{사용자}/**` | 해당 개발자 | 검증용 산출물 |
| 코드 | 앱 소스 트리 | 해당 개발자 | — |

## 11. 왜 루트 컨텍스트를 관리자만 만지는가

루트 `AGENTS.md`와 `CLAUDE.md`, 그리고 `.docs/root-context/`의 복사본은 성질이 이렇다.

1. 모든 세션에 무조건 로드된다. 여기에 잘못된 경로나 불필요한 규칙이 들어가면 모든 사람의 모든 작업에 영향을 준다. 앱별 instruction의 오류가 그 앱 작업에만 영향을 주는 것과 범위가 다르다.
2. 내용이 개발 지식이 아니다. 앱 목록, 문서 경로, 산출물 위치 표, portable routing 참조가 전부다. 도메인을 아는 사람이 쓸 이유가 없다. 하네스 구조를 아는 사람이 써야 한다.
3. 스킬이 생성·갱신하는 관리 블록을 갖는다. `harness-kit:managed:start` / `end` 마커 안쪽은 `harness-setup` 재실행 시 갱신되는 영역이다. 이걸 모르고 손으로 고치면 다음 갱신에서 되돌아간다. 갱신 자체가 사용자 수정으로 오인돼 멈추기도 한다.
4. 복수 레포 구조에서는 어떤 git에도 속하지 않는다. 리뷰도 이력도 남지 않는다. 잘못 바뀌어도 누가 언제 바꿨는지 추적할 수단이 없으므로 애초에 만지는 사람을 좁히는 것 외에는 통제 수단이 없다.

`.docs/harness/**`도 같은 이유다. 이 번들은 "무엇을 승인해야 쓸 수 있는가"를 정의하는 쪽이다. 승인 규칙을 지켜야 하는 사람이 승인 규칙 자체를 고칠 수 있으면 계약이 성립하지 않는다.

## 12. 왜 설계·컨텍스트·지침은 PL·대리급이 관리하는가

`{앱}/context-base/**`, `{앱}-context.md`, `{앱}/instruction/**`는 성격이 다르다. 이 문서들은 **팀 전체의 코드 결과물을 결정한다.** 에이전트는 매 작업마다 이 문서를 읽고 그대로 코드를 만들기 때문에 여기 적힌 규칙 한 줄이 그날 팀이 만든 모든 코드에 반영된다. 사람에게 주는 코딩 가이드와 강제력이 다르다.

그래서 이 계층은 아키텍처 결정 권한이 있는 사람, 즉 설계를 리딩하는 PL·대리급이 관리한다.

- 일관성: 세 앱에 걸친 데이터 표준이나 API 규약은 앱 담당자가 각자 쓰면 서로 어긋난다.
- 변경 파급: instruction 한 줄 수정은 이후 생성될 모든 코드에 적용된다. 코드 리뷰 한 건보다 파급이 크다.
- 판단 필요: `context-doc`은 설계 문서에 있는 주제만 문서로 만들고 없는 내용은 `미정`으로 남긴다. 그 `미정`을 무엇으로 채울지는 설계 결정이다.

개발자는 이 계층을 읽고 따른다. 바꿔야 한다고 판단하면 직접 고치지 않고 리딩에게 변경을 제안한다. 개발자가 직접 소유하는 것은 자기 이름이 붙은 `impl-doc/{사용자}/`와 `prototype/{사용자}/`, 그리고 실제 코드다.

## 13. 왜 앱별 impl 문서는 해당 개발자가 관리하는가

`impl-doc`과 `impl-fe-be-doc`이 만드는 문서는 팀 공통 규칙이 아니라 실제 구현을 위한 작업 문서다. 어떤 기능을 어떤 순서로 만들지, 기존 코드에서 무엇을 재사용할지, 어떤 검증을 통과해야 완료로 볼지를 기록한다. 구현 중 발견한 제약과 변경 사항도 이 문서에 가장 먼저 반영된다. 따라서 문서의 작성·갱신·진행 상태 관리는 실제 구현을 맡은 개발자가 책임진다.

앱별 소유 경로는 다음과 같다.

| 담당 앱 | 개발자 소유 경로 |
|---|---|
| `fe-exam-portal` | `.docs/fe-exam-portal/impl-doc/{사용자}/**` |
| `be-exam-portal` | `.docs/be-exam-portal/impl-doc/{사용자}/**` |
| `be-exam-collector` | `.docs/be-exam-collector/impl-doc/{사용자}/**` |

여기서 소유권은 혼자 결정한다는 뜻이 아니다. PL과 리뷰어는 구현 방향과 완료 기준을 검토할 수 있지만, 담당 개발자의 작업 문서를 알리지 않고 대신 고치거나 진행 상태를 대신 관리하지 않는다. 여러 개발자가 함께 구현하는 기능도 앱별 경로를 먼저 나눈 뒤 각 담당자의 폴더에서 관리하고, 앱 간 의존성과 인계 조건을 문서에 서로 연결한다.

구현 중 발견한 내용이 앱 전체의 아키텍처, API 계약, 코딩 규칙을 바꾸는 결정이라면 개인 `impl-doc`에만 남겨 두지 않는다. PL·대리급 개발 리딩에게 제안해 `DESIGN.md`나 `instruction/**`의 팀 공용 기준으로 승격한다. 반대로 다른 플러그인이 구현 계획이나 검증 문서를 만들더라도 산출물은 `artifact-output-routing-instruction.md`가 정한 해당 앱·사용자 경로에 저장한다.

## 14. 미정 — 소유권을 강제하는 방법

여기까지가 누가 무엇을 소유하는가를 정한 기준이다. 이 기준을 실제로 어떻게 강제할지, 즉 규약 문서로만 둘지, 레포 권한이나 CODEOWNERS로 막을지, `.docs/harness/`의 write guard로 처리할지, 아니면 리뷰 절차로 흡수할지는 아직 정하지 않았다.

각 방식은 구조에 따라 적용 가능 여부가 다르다.

- 복수 레포 구조에서 루트 `AGENTS.md` / `CLAUDE.md`는 어떤 git에도 속하지 않으므로 레포 권한이나 CODEOWNERS로 막을 수 없다.
- 단일 레포 구조에서는 두 파일이 레포 안에 있으므로 레포 차원의 통제가 가능하다.
- `.docs/harness/`의 host hook은 `active` 상태여야 동작한다. 그마저도 완전한 차단 장치가 아니다.

**이 절은 다음 논의에서 채운다.** 현재 시점에서 확정된 것은 소유권 구분과 그 근거까지다.

---

# 제3부. 단일 레포 × 복수 애플리케이션

## 15. 한눈에 보기

한 개의 git 레포 안에 애플리케이션 폴더가 여러 개 있는 구조다. 문서 흐름의 골격은 제1부와 같다. 달라지는 것은 git 경계와 그에 따라오는 소유권·공유 방식이다.

### 15.1 스킬 실행 순서

단일 레포에서도 문서 구조를 만드는 `harness-setup`, `design-doc`, `context-doc`의 역할은 동일하다. Git 작성자 계정 확인도 필수지만, `git-scoped-account`는 git으로 관리하지 않는 컨테이너 바로 아래의 복수 앱 레포를 대상으로 하므로 단일 레포에서는 대상 0건으로 끝난다. 이 경우 네 번째 역할은 해당 레포의 로컬 `user.name`·`user.email` 설정과 출처 확인으로 대체한다.

```text
[필수 역할 4개]
1. harness-setup            모노레포의 복수 앱 문서 골격과 루트 컨텍스트 생성
2. Git 계정 확인            git-scoped-account 대신 이 레포의 로컬 계정 설정·출처 확인
3. design-doc               앱별 DESIGN.md 작성
4. context-doc              앱별 *-context.md와 instruction 세트 작성

[네 역할 이후 — 플러그인 선택 자유]
구현 계획·프로토타입·실제 구현은 다른 플러그인이나 도구를 사용해도 된다.
산출물의 정본 경로와 앱·사용자별 소유권만 이 프로젝트의 라우팅 계약을 따른다.
```

### 15.2 최종 구조

```text
exam/                                     ← 단일 git 레포 (루트에서 git init)
├── .git/
├── .gitignore
├── AGENTS.md                             ← 공통 AI 컨텍스트 정본 (레포에 커밋됨)
├── CLAUDE.md                             ← @AGENTS.md bridge (레포에 커밋됨)
│
├── fe-exam-portal/                       ← 프론트엔드 앱 폴더 (별도 레포 아님)
├── be-exam-portal/                       ← 포털 백엔드 앱 폴더
├── be-exam-collector/                    ← 외부 데이터 수집 배치 앱 폴더
│
└── .docs/                                ← 같은 레포 안의 문서 디렉토리 (별도 레포 아님)
    ├── README.md
    ├── .gitignore                        ← 이 레포의 중첩 .gitignore로 동작
    ├── _inbox/
    ├── .harness/                         ← 문서 개선·쓰기 승인 내부 상태
    ├── root-context/
    │   ├── AGENTS.md
    │   └── CLAUDE.md
    ├── harness/
    │   ├── README.md
    │   ├── artifact-routing.json
    │   ├── artifact-format-contract.json
    │   ├── install-routing.ps1
    │   ├── normalize-artifact.ps1
    │   └── hooks/
    │
    ├── fe-exam-portal-context.md
    ├── fe-exam-portal/
    │   ├── context-base/DESIGN.md
    │   ├── instruction/*.md
    │   └── impl-doc/{사용자}/*.md
    │
    ├── be-exam-portal-context.md
    ├── be-exam-portal/
    │   ├── context-base/DESIGN.md
    │   ├── instruction/*.md
    │   └── impl-doc/{사용자}/*.md
    │
    ├── be-exam-collector-context.md
    ├── be-exam-collector/
    │   ├── context-base/DESIGN.md
    │   ├── instruction/*.md
    │   └── impl-doc/{사용자}/*.md
    │
    └── prototype/{사용자}/{식별자}/
```

제1부와 달라지는 곳은 아래 세 군데가 전부다.

| 항목 | 복수 레포 | 단일 레포 |
|---|---|---|
| 루트 `AGENTS.md` / `CLAUDE.md` | 어떤 git에도 속하지 않음 | 레포에 커밋됨. 브랜치·리뷰·이력이 남는다 |
| `.docs` | 별도 git 레포. 따로 clone·push | 같은 레포 안. 코드와 함께 커밋된다 |
| git 계정 | 앱 레포마다 설정 필요 | 레포 하나에만 설정하면 된다 |

### 15.3 에이전트가 문서를 읽는 순서

읽는 순서 자체는 제1부와 동일하다.

```text
[세션 시작 — 자동 로드]
  Claude Code : exam/CLAUDE.md → @AGENTS.md 인라인 확장
  Codex       : exam/AGENTS.md

[작업 대상 앱 확정 후]
  .docs/{앱}-context.md → 지침 인덱스의 @ 참조 → .docs/{앱}/instruction/*.md

[쓰기 직전]
  .docs/{앱}/instruction/artifact-output-routing-instruction.md
  .docs/harness/artifact-routing.json
```

다만 단일 레포에서는 앱 폴더에서 세션을 여는 일이 흔하다. 그러면 루트 `CLAUDE.md` / `AGENTS.md`가 자동 로드되지 않거나 앱 폴더 기준으로 잡혀 컨텍스트가 반쯤 빠진 채 작업이 시작된다. **세션은 레포 루트(`exam/`)에서 연다**는 규칙을 팀 규약으로 명시해 두는 편이 안전하다.

---

## 16. 0단계 — 레포 준비

```bash
git clone {레포 주소} exam
```

복수 레포와 달리 clone 한 번으로 앱과 문서가 함께 따라온다. `.docs`를 따로 clone할 필요도, 앱을 개별로 clone할 필요도 없다. 단일 레포 구조의 가장 큰 장점이 여기 있다. 새로 합류한 사람이 문서 절반만 갖고 시작하는 사고가 생기지 않는다.

새 프로젝트라면 레포 루트에서 `git init` 후 앱 폴더를 만든 뒤 `harness-setup`을 실행한다.

---

## 17. 1단계 — `harness-setup` (권장·강제)

```text
Codex        : $harness-setup
Claude Code  : /harness-kit:harness-setup
```

이 구조에서는 판정 단계에 한 번 더 확인이 붙는다. `harness-setup`은 루트에 빌드 매니페스트가 있으면서 하위에도 앱 후보가 여러 개면 모노레포 가능성으로 보고 사용자에게 직접 묻는다.

> 탐색 결과 루트에도 매니페스트가 있고 하위 앱 후보가 3개입니다. 복수 애플리케이션으로 세팅할까요?

여기서 복수 애플리케이션으로 승인하면 제1부와 같은 앱별 골격(`{앱}-context.md`, `{앱}/context-base/`, `{앱}/instruction/`, `{앱}/impl-doc/`)이 만들어진다. 단일 애플리케이션으로 승인하면 `.docs/context-base/`, `.docs/instruction/`처럼 앱 구분 없는 평평한 구조가 된다. 나중에 앱별로 쪼개려면 문서를 옮기는 작업이 따로 필요하다. **앱이 실제로 여러 개라면 처음부터 복수 애플리케이션으로 세팅한다.**

`.docs/.gitignore`는 이 레포의 중첩 `.gitignore`로 동작한다. 별도 레포의 루트 `.gitignore`가 아니다. `_inbox/` 내용이 커밋되지 않는 동작은 동일하다.

---

## 18. 2단계 — git 계정 처리

`git-scoped-account`가 대상으로 삼는 것은 컨테이너 바로 아래 1단계 앱 레포들이다. 단일 레포 구조에는 그런 하위 레포가 없으므로 탐지 결과가 0건이 되고 스킬은 이유를 알린 뒤 종료한다. 이 구조에서는 실행하지 않아도 된다.

레포별로 계정을 분리해야 한다면 해당 레포에서 로컬 설정을 쓴다.

```bash
git config --local user.name "{이름}"
```

```bash
git config --local user.email "{메일}"
```

전역 설정으로 충분하다면 이 단계 자체를 건너뛴다.

---

## 19. 3단계 — `design-doc`로 앱별 설계 맥락 만들기

제1부 5절과 동일하다. 앱마다 한 번씩 수행한다. 산출물은 앱별 `context-base/`에 저장된다.

| 대상 앱 | 산출물 |
|---|---|
| `fe-exam-portal` | `.docs/fe-exam-portal/context-base/DESIGN.md` |
| `be-exam-portal` | `.docs/be-exam-portal/context-base/DESIGN.md` |
| `be-exam-collector` | `.docs/be-exam-collector/context-base/DESIGN.md` |

차이는 리뷰 경로다. `.docs`가 소스와 같은 레포에 있으므로 설계 문서 변경도 코드와 같은 브랜치·PR에 얹을 수 있다. 설계 변경과 그것을 반영한 코드를 한 PR에서 함께 본다는 뜻이다. 이 구조에서 실제로 노려야 할 이점이 여기 있다.

---

## 20. 4단계 — `context-doc`로 컨텍스트와 지침 만들기

산출물 종류, 기본 instruction 목록, 추가 주제를 요청하는 방법, 질문 예산 3회 제한은 제1부 6절과 완전히 동일하다. 여기서는 결과 구조만 다시 보인다.

```text
exam/
├── AGENTS.md                             ← 앱 목록·경로 지도 (레포에 커밋)
├── CLAUDE.md                             ← @AGENTS.md bridge (레포에 커밋)
├── fe-exam-portal/
├── be-exam-portal/
├── be-exam-collector/
└── .docs/
    ├── root-context/
    │   ├── AGENTS.md                     ← context-doc이 갱신, harness-setup이 루트에 반영
    │   └── CLAUDE.md
    ├── harness/
    │
    ├── fe-exam-portal-context.md
    ├── fe-exam-portal/
    │   ├── context-base/DESIGN.md
    │   ├── instruction/
    │   │   ├── agent-instruction.md
    │   │   ├── artifact-output-routing-instruction.md
    │   │   ├── architecture-instruction.md
    │   │   ├── framework-instruction.md
    │   │   ├── api-instruction.md
    │   │   ├── file-convention-instruction.md
    │   │   └── data-standard-instruction.md
    │   └── impl-doc/
    │
    ├── be-exam-portal-context.md
    ├── be-exam-portal/
    │   ├── context-base/DESIGN.md
    │   ├── instruction/
    │   │   ├── agent-instruction.md
    │   │   ├── artifact-output-routing-instruction.md
    │   │   ├── api-instruction.md
    │   │   └── data-standard-instruction.md
    │   └── impl-doc/
    │
    ├── be-exam-collector-context.md
    ├── be-exam-collector/
    │   ├── context-base/DESIGN.md
    │   ├── instruction/
    │   │   ├── agent-instruction.md
    │   │   ├── artifact-output-routing-instruction.md
    │   │   ├── architecture-instruction.md
    │   │   ├── code-style-instruction.md
    │   │   └── data-standard-instruction.md
    │   └── impl-doc/
    │
    └── prototype/
```

---

## 21. `.docs/harness/`가 고정하는 것

내용은 제1부 7절과 같다. `artifact-routing.json`의 `project_root`와 `mode` 값이 이 프로젝트 형태를 반영하고 앱별 `source_root`가 레포 루트 기준 상대 경로가 된다는 점만 다르다.

단일 레포에서 추가로 주의할 것은 앱 경계를 넘는 쓰기다. 물리적으로 같은 레포이므로 에이전트가 `be-exam-portal/`을 고치다가 `fe-exam-portal/`까지 손대기가 쉽다. 복수 레포에서는 최소한 레포 경계가 사고를 한 번 걸러 주지만 여기에는 그 장치가 없다. 앱별 라우팅 instruction의 "앱 A에서 앱 B의 경로에 쓰지 않는다" 규칙이 이 구조에서 훨씬 더 중요해진다.

---

## 22. 개발자별 산출물은 어디에 생기는가

경로 규칙은 제1부 8절과 동일하다.

| 대표 producer | 산출물 위치 |
|---|---|
| `impl-doc` / `impl-fe-be-doc` | `.docs/{앱}/impl-doc/{사용자}/{YYMMDD}-{순번}.{기능}-impl-{종류}.md` |
| 로드맵 인덱스 | `.docs/{앱}/impl-doc/{사용자}/{YYMMDD}-0.{앱이름}-roadmap-impl-index.md` |
| `create-prototype` | `.docs/prototype/{사용자}/{식별자}/` |

표에 적힌 스킬은 대표 예시일 뿐 필수 도구가 아니다. 다른 플러그인의 유사 스킬이 만든 구현 계획·프로토타입도 동일하게 `_inbox`로 먼저 받고 승인된 경로로만 정본에 반영한다. 실제 구현 역시 어떤 코딩 플러그인이나 도구를 사용해도 되지만 변경 대상은 해당 앱의 source tree를 벗어나지 않는다.

단일 레포이므로 여기서는 커밋 위생이 추가 과제가 된다. 구현 계획 문서와 실제 코드 변경이 같은 레포에 있으므로 무엇을 같은 커밋에 넣고 무엇을 나눌지 팀 규약이 없으면 문서 변경이 코드 리뷰를 덮어버린다. 최소한 문서 전용 커밋과 코드 커밋을 나누는 정도는 정해 두는 편이 좋다.

---

## 참조 문서

| 문서 | 역할 |
|---|---|
| [Plugin_Installation_Guide.md](./Plugin_Installation_Guide.md) | 플러그인 설치·확인·업데이트·제거 |
| [Harness_Engineering.md](./Harness_Engineering.md) | 사용자·관리자 운영 정본, 스킬 전체 맵 |
| [Harness_Engineering_Intro.md](./Harness_Engineering_Intro.md) | 하네스 도입 배경과 사용 예시 |
