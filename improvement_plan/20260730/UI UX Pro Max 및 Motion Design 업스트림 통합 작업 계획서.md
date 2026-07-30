# UI/UX Pro Max 및 Motion Design 업스트림 통합 작업 계획서

> 생성 기준: `skills/impl-doc`
> 프로젝트 유형: AI Agent 사용자 플러그인·외부 업스트림·디자인 하네스 리팩토링
> 대상 저장소: `ai-agent-harness-docs`
> 작성일: 2026-07-30
> 상태: 구현 전 계획
> 선행 계획: `improvement_plan/20260729/플러그인 전환 및 스킬 거버넌스 리팩토링 작업 계획서.md`

---

## 0. 문서 목적

이 문서는 다음 작업을 Phase 단위로 구현·검증·커밋하기 위한 실행 계획이다.

1. UI/UX Pro Max와 Motion Design을 사용자 플러그인의 독립 스킬로 반입한다.
2. 두 업스트림의 유용한 원칙을 기존 디자인·구현·검증 스킬에도 참고형으로 반영한다.
3. 같은 GitHub 원본을 직접 반입형과 참고형으로 동시에 안전하게 최신화할 수 있도록 관리자 거버넌스를 보완한다.
4. 기존 일반 하네스 흐름과 구분되는 디자인 전용 흐름을 추가한다.
5. 디자인 전용 흐름은 프로토타입과 실제 제품 화면 구현의 두 갈래로 분기한다.
6. Caveman과 Ruflo는 하네스 플러그인에 내장하지 않고 별도 설치 대상으로 문서화한다.
7. `README.md`, `Docs/Harness_Engineering_Intro.md`, `Docs/Harness_Engineering.md`와 관련 운영 문서를 현재 구조에 맞게 갱신한다.

이 계획서는 구현 결과물이 아니다. 외부 파일 반입, 보호 자산 추가·변경, 플러그인 재생성은 각 Phase의 승인·검증 조건을 충족한 뒤 수행한다.

---

## 1. 관리자의 의도

### 1-1. 사용자에게 보일 최종 형태

- 사용자는 `ai-agent-harness` 플러그인 하나를 설치한다.
- 설치된 플러그인에서 `ui-ux-pro-max`와 `motion-design`을 독립 스킬로 호출할 수 있다.
- 사용자는 원본 GitHub 저장소를 별도로 clone하거나 그 안의 상대경로를 알 필요가 없다.
- 두 스킬은 Codex와 Claude에서 같은 논리 이름과 같은 핵심 동작을 제공한다.
- 실제 실행은 플러그인에 포함된 승인·고정된 로컬 스냅샷만 사용한다.
- 사용자 실행 중 GitHub `main`을 직접 읽거나 최신 파일을 자동 덮어쓰지 않는다.
- 최신화는 관리자가 이 저장소에서 검토·승인·검증한 뒤 새 플러그인 버전으로 배포한다.

### 1-2. 원본 자료 사용 의도

독립 스킬로 반입할 때 `SKILL.md` 한 파일만 가져오지 않는다.

- UI/UX Pro Max는 검색 스크립트, 디자인 데이터, 빠른 참조, 규칙 자료 등 실제 동작에 필요한 묶음을 함께 관리한다.
- Motion Design은 `director/`, `patterns/`, `reference/`의 전체 지식 묶음을 함께 관리한다.
- 원본 자산은 출처·파일 대응표·선택한 SHA·라이선스·로컬 수정 내용을 기록한다.
- 템플릿, 스크립트, 데이터, references, examples, evals는 보호 자산으로 취급한다.
- 보호 자산의 추가·수정·보완은 영향 보고와 승인을 거친다.
- 보호 자산의 삭제·이동·교체는 별도의 파괴적 변경 승인 없이는 수행하지 않는다.

### 1-3. 직접 반입과 참고 반영의 구분

같은 외부 저장소를 다음 두 방식으로 동시에 사용한다.

| 구분 | 목적 | 사용자 플러그인 포함 | 최신화 방식 |
|---|---|---:|---|
| 직접 반입형 `adapted` | 독립 스킬과 전체 실행 자산 제공 | 포함 | 원본 파일·해시·라이선스·로컬 변환을 비교 |
| 참고형 `reference` | 기존 하네스 스킬에 검증된 원칙만 반영 | 외부 원문은 미포함 | 의미 단위 차이를 비교하고 필요한 원칙만 제안 |

참고형 반영은 다른 스킬 내부의 상대경로나 구현 파일에 결합하지 않는다. 기존 스킬에는 필요한 핵심 원칙과 공개 스킬 이름을 통한 handoff만 남긴다.

### 1-4. 별도 설치 대상

다음 프로젝트는 이번 사용자 플러그인에 포함하지 않는다.

- [Caveman](https://github.com/JuliusBrussee/caveman): 응답 표현과 토큰 사용 방식을 바꾸는 별도 플러그인·스킬이다. 하네스의 설계·검증 계약과 별개로 사용자가 원할 때 원본 안내에 따라 설치한다.
- [Ruflo](https://github.com/ruvnet/ruflo): 다중 에이전트, 메모리, MCP, hook 등을 포함하는 독립 메타 하네스다. 현재 하네스 플러그인 안에 일부만 복제하지 않고 원본 제품으로 별도 설치한다.

문서에는 변하기 쉬운 설치 명령을 임의로 복제하지 않는다. 구현 시점에 원본 README와 설치 문서를 확인하고, 링크와 “최신 설치 방법은 원본을 따른다”는 경계를 명시한다.

---

## 2. 확정 설계

### 2-1. 신규 사용자 스킬

| 로컬 스킬 | 업스트림 | 분류 | 기본 역할 |
|---|---|---|---|
| `ui-ux-pro-max` | [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | `reputable-third-party + adapted` | 제품 유형·스타일·색·타이포그래피·레이아웃·UX·접근성·기술 스택에 맞는 디자인 시스템 탐색 |
| `motion-design` | [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill) | `reputable-third-party + adapted` | 애니메이션 목적·타이밍·이징·동작 속성·안무·접근성·성능을 정하는 모션 설계 |

구현 후 사용자 스킬 수는 18종에서 20종으로 바뀐다.

- 사용자 논리 스킬: 20종
- Codex runtime 물리 스킬: 20종
- Claude runtime 물리 스킬: 20종
- runtime agent: 양쪽 모두 0종
- 관리자 스킬: 3종 유지

### 2-2. UI/UX Pro Max 반입 범위

업스트림은 현재 `src/ui-ux-pro-max/`를 정본으로 설명하고 `.claude/skills/ui-ux-pro-max/`를 생성·시험 표면으로 제공한다. 구현 시 선택한 안정 태그 또는 commit SHA에서 다음을 확인한다.

- `src/ui-ux-pro-max/**`
- `.claude/skills/ui-ux-pro-max/**`
- `skill.json`
- `.claude-plugin/plugin.json`
- `LICENSE`
- CLI의 자산 동기화·검증 계약

로컬 반입 대상은 실제 독립 스킬에 필요한 다음 묶음이다.

- 플랫폼 중립 `SKILL.md`
- 로컬 검색·디자인 시스템 생성 스크립트
- 제품 유형, 스타일, 색상, 타이포그래피, UX, 차트, 스택 데이터
- 빠른 참조와 품질 규칙
- 로컬 회귀검증용 eval

다음 형제 스킬은 이 Phase에서 함께 반입하지 않는다.

- `banner-design`
- `brand`
- `design-system`
- `design`
- `slides`
- `ui-styling`

이들은 기능 중복, 별도 출처, 라이선스, 의존 관계를 다시 확인해야 하므로 별도 후보로 남긴다.

### 2-3. Motion Design 반입 범위

선택한 commit SHA에서 다음 묶음을 하나의 보호 자산 단위로 반입한다.

- `skills/motion-design/SKILL.md`
- `skills/motion-design/director/**`
- `skills/motion-design/patterns/**`
- `skills/motion-design/reference/**`
- `LICENSE`

원본 자료는 유지하되 로컬 `SKILL.md`와 필요한 보완 자료에는 다음 하네스 기준을 적용한다.

- 모션은 장식보다 정보 전달·상태 변화·방향 안내·피드백 목적을 우선한다.
- 정적 화면이나 기존 디자인 시스템만으로 충분하면 모션 단계를 건너뛸 수 있다.
- 모든 화면에 primary·secondary·ambient 모션을 강제하지 않는다.
- 공공·의료·금융·엔터프라이즈 화면은 낮은 모션 밀도를 기본값으로 둔다.
- `prefers-reduced-motion`과 동등한 대체 전달 수단을 필수 검토한다.
- transform·opacity를 우선하되, 의미와 플랫폼 특성상 다른 속성이 필요한 경우 근거와 성능 검증을 요구한다.
- 기존 제품의 디자인 토큰과 모션 언어가 있으면 새 규칙보다 우선한다.

### 2-4. 업스트림 관계 ID

현재 레지스트리는 source 하나당 `integration_mode` 하나를 가지므로 직접 반입과 참고 반영을 별도 source 관계로 기록한다.

| 관계 ID 제안 | 모드 | 로컬 대상 | 패키징 |
|---|---|---|---:|
| `ui-ux-pro-max-runtime` | `adapted` | `ui-ux-pro-max` | 포함 |
| `ui-ux-pro-max-principles` | `reference` | 기존 디자인·구현·검증 스킬 | 미포함 |
| `lottiefiles-motion-design-runtime` | `adapted` | `motion-design` | 포함 |
| `lottiefiles-motion-design-principles` | `reference` | 기존 디자인·구현·검증 스킬 | 미포함 |

같은 저장소에서 파생된 두 관계는 다음 값을 공유해야 한다.

- repository URL
- accepted upstream tag 또는 commit SHA
- observed commit SHA
- 라이선스 판정 기준
- 최신화 candidate ID 또는 relationship group

한 관계만 새 SHA로 승격되어 직접 반입 내용과 참고 원칙이 어긋나는 상태를 허용하지 않는다.

### 2-5. 기존 스킬 참고 반영

| 기존 스킬 | UI/UX Pro Max에서 참고할 내용 | Motion Design에서 참고할 내용 |
|---|---|---|
| `design-prototype-docs` | 제품 유형, 화면 밀도, 디자인 토큰, 색·타이포그래피·간격, 반응형·접근성 상태 | 모션 목적, 상태 전환, 우선순위, reduced-motion 대체안 |
| `create-prototype` | 선택된 디자인 토큰과 반응형·상태 피드백을 검증 시안에 반영 | 승인된 모션 후보만 시안에서 검증하고 과도한 반복·장식을 피함 |
| `frontend-design` | 기존 디자인 시스템 우선, 스택별 구현 원칙, 접근성·일관성 검사 | 확정된 모션 명세를 제품 코드로 구현하고 성능·reduced-motion을 보장 |
| `impl-verify` | 대비, focus, touch target, overflow, 상태, 토큰 일관성 | reduced-motion, 프레임 저하, 반복 피로, 핵심 정보 전달, 정지 상태를 검증 |

`frontend-design`은 이미 Anthropic 직접 변환본이므로 전체 분류는 계속 `adapted`다. 새 두 출처는 그 스킬의 참고 source 목록에 추가한다. 나머지 세 스킬은 `reference` 분류를 유지한다.

### 2-6. 디자인 전용 하네스 흐름

일반 하네스 전체 흐름 안에 모든 디자인 세부 단계를 강제로 넣지 않는다. UI가 포함된 작업에서 선택하는 별도 흐름을 제공한다.

```mermaid
flowchart TD
    R["승인된 요구사항 또는 design-doc"] --> U["ui-ux-pro-max<br/>디자인 방향·시스템"]
    U --> S["design-prototype-docs<br/>화면·상태·반응형 명세"]
    S --> M{"모션이 필요한가?"}
    M -->|"예"| MD["motion-design<br/>목적·타이밍·대체안"]
    M -->|"아니오"| B{"최종 목적"}
    MD --> B

    B -->|"검증용 프로토타입"| P["create-prototype<br/>.docs/prototype의 폐기 가능 시안"]
    P --> A{"사용자 검토"}
    A -->|"프로토타입만 필요"| PV["impl-verify<br/>시안·요구사항 검증"]
    A -->|"실제 화면 구현 승인"| F["frontend-design<br/>제품 소스 구현"]

    B -->|"실제 제품 화면"| F
    F --> V["impl-verify<br/>기능·UI·접근성·모션 검증"]
```

분기 규칙:

- 프로토타입 분기 산출물은 `.docs/prototype/**`의 폐기 가능한 검증 자료다.
- 프로토타입 HTML/CSS/JS를 실제 제품 소스로 복사하거나 승격하지 않는다.
- 프로토타입 승인 후 실제 구현으로 넘어갈 때는 승인된 디자인 결정과 화면 명세만 `frontend-design`에 전달한다.
- 사용자가 처음부터 실제 화면 구현을 요청하면 `create-prototype`을 강제하지 않는다.
- 실제 화면 구현은 반드시 제품 repository의 기존 컴포넌트·토큰·프레임워크를 먼저 조사한다.
- 두 분기 모두 최종 목적에 맞는 `impl-verify` 검증을 수행한다.

### 2-7. 신규 스킬의 호출 기준

`ui-ux-pro-max`를 호출할 때:

- 새 제품·화면의 디자인 방향을 정할 때
- 색상, 타이포그래피, 간격, 레이아웃, 컴포넌트 밀도를 정할 때
- 제품 유형이나 업종에 맞는 디자인 시스템 후보가 필요할 때
- 기존 화면의 UX·접근성·일관성을 리뷰할 때
- React, Vue, Flutter 등 기술 스택별 UI 원칙이 필요할 때

호출하지 않아도 되는 경우:

- 백엔드 전용 작업
- 기존 디자인 시스템과 화면 명세가 이미 확정되어 단순 구현만 남은 경우
- 디자인 판단 없이 문구나 데이터만 수정하는 경우

`motion-design`을 호출할 때:

- 진입·퇴장·페이지 전환·모달 전환을 설계할 때
- loading·success·error·hover·press 같은 상태 피드백이 필요할 때
- 여러 요소의 등장 순서와 시선을 설계할 때
- 브랜드 모션 언어를 만들 때
- 기존 애니메이션의 속도·이징·피로감·접근성을 리뷰할 때

호출하지 않아도 되는 경우:

- 정적 화면으로 목적이 충분한 경우
- 모션이 요구사항에 없고 추가 효과가 오히려 방해되는 경우
- 기존 제품 모션 명세를 그대로 적용하면 되는 단순 구현

---

## 3. 변경 표면

### 3-1. 사용자 스킬 정본

- `skills/ui-ux-pro-max/**` 신규
- `skills/motion-design/**` 신규
- `skills/design-prototype-docs/**` 참고 원칙·handoff 보완
- `skills/create-prototype/**` 참고 원칙·분기 경계 보완
- `skills/frontend-design/**` 참고 원칙·제품 구현 경계 보완
- `skills/impl-verify/**` 디자인·모션 검증 보완

### 3-2. 관리자 거버넌스 정본

- `maintainer/skills/skill-portfolio-maintainer/**`
- `maintainer/skills/harness-plugin-maintainer/**`
- 필요성이 확인된 경우에만 `maintainer/skills/custom-skill-design/**`
- `maintainer/upstreams/schema.json`
- `maintainer/upstreams/registry.json`
- `maintainer/upstreams/lock.json`
- `maintainer/upstreams/provenance/current-skills.json`
- `maintainer/upstreams/provenance/{신규-source}/**`
- `maintainer/upstreams/candidates/**`
- `maintainer/upstreams/promotions/**`
- `maintainer/inventory/retained-skill-audit.json`
- `maintainer/inventory/markdown-artifact-flow.json`

### 3-3. 플러그인 생성·검증 표면

- `maintainer/plugin/CAPABILITIES.json`
- `maintainer/plugin/runtime-allowlist.json`
- `maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py`
- `maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py`
- 관련 build·install·release regression fixture
- `plugins/ai-agent-harness/**` 생성물
- release archive·checksum·metadata

`plugins/ai-agent-harness/**`는 직접 편집하지 않고 builder로 재생성한다.

### 3-4. 관리자 projection

- `.agents/skills/**`
- `.claude/skills/**`

projection은 관리자 정본 변경 후 다음 생성기로만 갱신한다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
```

신규 사용자 스킬은 관리자 projection에 포함하지 않는다.

### 3-5. 운영 문서

필수:

- `README.md`
- `Docs/Harness_Engineering_Intro.md`
- `Docs/Harness_Engineering.md`

연쇄 갱신:

- `Docs/README.md`
- `Docs/Plugin_Installation_Guide.md`
- `Docs/Imported_Skill_Provenance.md`
- `Docs/External_Skill_References.md`
- `Docs/Skill_Upstream_Update_Policy.md`
- `maintainer/README.md`
- 관련 `example/**`

역사 문서인 `improvement_plan/20260627/**`는 수정하지 않는다.

---

## 4. 공통 승인·보호 규칙

### 4-1. 승인 게이트

| 게이트 | 필요한 시점 | 승인 내용 |
|---|---|---|
| upstream 선정 승인 | 태그·SHA와 반입 범위를 확정할 때 | 저장소, 버전, 파일 범위, 분류 |
| 일반 반영 승인 | staging 분석이 끝났을 때 | 직접 반입·참고 반영 내용 |
| 보호 자산 영향 승인 | scripts, data, references, templates, examples, evals 추가·변경 시 | 추가·수정·보완 파일과 영향 |
| 파괴적 변경 승인 | 기존 또는 업스트림 보호 자산 삭제·이동·교체 시 | 정확한 파일 목록과 복구 방법 |
| 라이선스 승인 | 라이선스가 바뀌거나 재배포 조건이 불명확할 때 | 계속 반입·차단·대체 |

신규 스킬 구현은 보호 자산 추가가 예정되어 있으므로 asset-impact approval을 구현 Phase의 선행 조건으로 둔다.

### 4-2. 금지 사항

- GitHub `main`의 최신 파일을 사용자 runtime에서 직접 다운로드하지 않는다.
- 선택한 SHA가 없는 상태로 packaged upstream을 만들지 않는다.
- UI/UX Pro Max의 형제 스킬을 묵시적으로 포함하지 않는다.
- Motion Design의 references 일부만 골라 원본 전체 규칙처럼 표시하지 않는다.
- 다른 스킬의 내부 상대경로를 기존 스킬에 하드코딩하지 않는다.
- 원본 텍스트를 많이 복사해 놓고 `reference`로 분류하지 않는다.
- prototype 코드를 제품 소스로 복사하지 않는다.
- Caveman이나 Ruflo를 `ai-agent-harness`의 runtime에 포함하지 않는다.
- 사용자 프로젝트에 `.agents/skills`, `.claude/skills`, `skills/`를 생성하지 않는다.

---

# 5. Phase별 구현 계획

## Phase 0. 기준선·업스트림·라이선스 확정

### 목표

구현 전에 현재 repository 기준선과 두 업스트림의 정확한 안정 버전, 정본 경로, 파일 목록, 라이선스, 실행 의존성을 고정한다.

### 태스크

#### CORE-001 — 현재 하네스 기준선 동결

대상:

- `skills/**`
- `maintainer/plugin/**`
- `maintainer/upstreams/**`
- `plugins/ai-agent-harness/**`
- `README.md`
- `Docs/**`

작업:

1. 현재 사용자 스킬 18종과 관리자 스킬 3종 목록을 기록한다.
2. Codex·Claude runtime이 각각 18 skills / 0 agents인지 확인한다.
3. 기존 디자인 흐름과 skill handoff를 기록한다.
4. 현재 Markdown producer 7종을 기록한다.
5. 관련 build·eval·install 검증의 PASS/FAIL을 기준선 보고서에 남긴다.

단독 검증:

- 현재 정본·projection·plugin 수가 문서와 일치한다.
- 작업 전 worktree의 사용자 변경을 분리해 기록한다.

#### IO-001 — UI/UX Pro Max upstream snapshot 조사

작업:

1. 최신 안정 release 또는 tag를 우선 확인한다.
2. 안정 release가 없거나 부적합하면 branch head SHA를 후보로 제시한다.
3. `src/ui-ux-pro-max/**` 정본과 생성된 `.claude/skills/ui-ux-pro-max/**`를 대조한다.
4. CLI asset sync 검사와 실제 생성 결과를 대조한다.
5. Python 스크립트의 파일 접근, network 사용, process 실행, 의존 패키지를 감사한다.
6. 데이터·references·templates의 전체 목록과 SHA-256을 만든다.
7. MIT LICENSE 원문과 hash를 저장한다.
8. 형제 스킬 6종이 반입 대상에서 제외됐는지 기록한다.

단독 검증:

- 선택 SHA와 모든 관찰 URL이 기록된다.
- 정본과 생성본 사이의 누락 파일이 설명된다.
- “원본 자료 전체 사용”의 범위가 파일 manifest로 증명된다.

#### IO-002 — Motion Design upstream snapshot 조사

작업:

1. release/tag 존재 여부를 확인하고 고정할 commit SHA를 선택한다.
2. `skills/motion-design/**` 전체 파일 목록과 SHA-256을 만든다.
3. `director/`, `patterns/`, `reference/`가 모두 포함됐는지 확인한다.
4. 실행 스크립트·외부 네트워크·도구 의존이 있는지 감사한다.
5. MIT LICENSE 원문과 hash를 저장한다.

단독 검증:

- 선택 SHA와 원본 트리 manifest가 일치한다.
- 누락된 참고 자료가 없다.

#### TEST-001 — Phase 0 기준선 검증

검증:

```bash
python maintainer/skills/skill-portfolio-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
git diff --check
```

### Phase 0 완료 기준

- [ ] 두 업스트림의 선택 버전과 SHA가 확정됐다.
- [ ] 원본 정본·생성본·실행 자산 대응표가 있다.
- [ ] 라이선스와 재배포 가능 여부가 확인됐다.
- [ ] 보호 자산 영향 목록이 승인 대기 상태로 분리됐다.
- [ ] 현재 18-skill 기준선 검증 결과가 저장됐다.

---

## Phase 1. 업스트림 거버넌스와 관리자 스킬 보완

### 목표

같은 GitHub 저장소를 직접 반입형과 참고형으로 동시에 추적하되 두 관계의 SHA가 어긋나지 않도록 관리자 workflow를 확장한다.

### 태스크

#### CORE-002 — registry relationship group 계약 추가

대상:

- `maintainer/upstreams/schema.json`
- `maintainer/upstreams/registry.json`
- registry loader·validator

작업:

1. 같은 repository의 관계들을 묶는 명시적 group 또는 pair 필드를 설계한다.
2. group 안의 active 관계는 accepted·observed SHA가 같아야 한다.
3. repository URL과 license 판정이 불일치하면 검증을 실패시킨다.
4. runtime `adapted` 관계와 principles `reference` 관계가 동시에 최신화 candidate에 포함되도록 한다.
5. reference 관계가 plugin license packaging 대상으로 잘못 들어가지 않도록 유지한다.

단독 검증:

- 같은 group의 SHA 불일치 fixture가 실패한다.
- 정상 pair fixture는 통과한다.
- 서로 다른 저장소의 독립 source에는 영향을 주지 않는다.

#### CORE-003 — `skill-portfolio-maintainer` workflow 보완

대상:

- `maintainer/skills/skill-portfolio-maintainer/SKILL.md`
- 관련 scripts, prompts, templates, evals

작업:

1. 한 upstream에서 여러 integration relationship을 만들 수 있음을 설명한다.
2. 조사·staging은 GitHub upstream 하나씩 수행한다는 원칙을 유지한다.
3. 같은 upstream의 direct/reference 관계는 하나의 candidate로 원자적 승인·승격한다.
4. 직접 반입 파일 diff와 참고 원칙 semantic diff를 한 보고서 안에서 구분한다.
5. protected asset 영향과 destructive diff를 관계별·파일별로 분리한다.
6. 원본 자산의 추가·수정·삭제와 로컬 보완 자산을 구분한다.
7. UI/UX Pro Max와 Motion Design용 smoke prompt·행동 fixture를 registry에서 검증한다.

#### CORE-004 — `harness-plugin-maintainer` 계약 보완

대상:

- `maintainer/skills/harness-plugin-maintainer/SKILL.md`
- 관련 scripts·evals

작업:

1. 사용자 스킬 수를 하드코딩된 18이 아니라 capability inventory에서 파생하도록 개선한다.
2. 구현 완료 후 양 runtime의 20종 일치와 manager skill 미누출을 검증한다.
3. packaged `adapted` source의 LICENSE·NOTICE·lock closure를 두 신규 source에 적용한다.
4. references·data·scripts가 archive에서 누락되지 않는지 asset manifest를 검증한다.
5. 플랫폼별 runtime 내용이 byte-equivalent인지 허용된 manifest 차이를 제외하고 비교한다.

#### CORE-005 — `custom-skill-design` 영향 감사

작업:

1. direct/reference 이중 관계, 전체 자산 반입, 공개 skill-name handoff 규칙이 이미 표현되는지 점검한다.
2. 부족한 일반 설계 규칙이 있을 때만 관리자 정본을 보완한다.
3. UI/UX Pro Max나 Motion Design 전용 내용은 `custom-skill-design`에 넣지 않는다.

#### IO-003 — 신규 provenance skeleton과 candidate 생성

대상:

- `maintainer/upstreams/registry.json`
- `maintainer/upstreams/provenance/**`
- `maintainer/upstreams/candidates/**`

작업:

1. 네 source relationship을 등록한다.
2. 두 GitHub upstream별 하나의 candidate bundle을 만든다.
3. file-map에서 `verbatim`, `modified`, `excluded`, `local-only`, `reference-only`를 파일 단위로 기록한다.
4. NOTICE와 LICENSE를 직접 반입 관계에 연결한다.
5. 참고형 관계에는 copied file이 없음을 검증한다.

#### TEST-002 — 관리자 workflow 회귀검증

검증:

```bash
python maintainer/skills/skill-portfolio-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
git diff --check
```

추가 fixture:

- paired SHA 불일치 차단
- reference-only 관계의 plugin package 제외
- protected asset 무승인 승격 차단
- 같은 upstream의 관계 중 하나만 승격하는 요청 차단
- 두 upstream을 한 candidate로 섞는 요청 차단

### Phase 1 완료 기준

- [ ] direct/reference 관계를 같은 upstream snapshot으로 묶을 수 있다.
- [ ] 관리자 스킬의 책임 경계가 유지된다.
- [ ] projection에는 관리자 3종만 존재한다.
- [ ] 사용자 신규 스킬은 아직 plugin runtime에 포함되지 않는다.

---

## Phase 2. `ui-ux-pro-max` 독립 스킬 구현

### 목표

UI/UX Pro Max의 검색·데이터·참조 기능을 보존하면서 Codex·Claude 공용 하네스 규칙에 맞는 플랫폼 중립 사용자 스킬을 만든다.

### 선행 승인

- upstream 선정 승인
- 일반 반영 승인
- scripts·data·references·templates·evals 추가에 대한 보호 자산 영향 승인

### 태스크

#### CORE-006 — 플랫폼 중립 `SKILL.md` 작성

대상:

- `skills/ui-ux-pro-max/SKILL.md`

계약:

1. frontmatter에 특정 모델, agent fork, Claude 전용 경로를 넣지 않는다.
2. 자연어 디자인 요청과 명시 호출을 모두 지원한다.
3. 기존 프로젝트의 디자인 시스템과 컴포넌트를 먼저 조사한다.
4. 제품 유형, 업종, 대상 사용자, 플랫폼, 기술 스택, 접근성 요구를 확인한다.
5. 검색 결과를 디자인 결정과 근거로 변환한다.
6. 디자인을 직접 구현할지, 문서화할지, 프로토타입으로 검증할지 구분한다.
7. 실제 제품 구현은 공개 이름 `frontend-design`으로 handoff한다.
8. 프로토타입 문서는 `design-prototype-docs`, 검증 시안은 `create-prototype`으로 handoff한다.
9. 모션이 필요할 때만 공개 이름 `motion-design`을 제안한다.
10. 외부 sibling skill의 내부 파일을 요구하지 않는다.

#### IO-004 — 검색·데이터·참조 자산 반입과 경로 중립화

대상:

- `skills/ui-ux-pro-max/scripts/**`
- `skills/ui-ux-pro-max/data/**`
- `skills/ui-ux-pro-max/references/**`
- 필요한 플랫폼 중립 보조 자산

작업:

1. 선택 SHA의 full manifest와 로컬 tree를 대응시킨다.
2. `${CLAUDE_PLUGIN_ROOT}`나 `.claude/skills` 전용 경로를 제거한다.
3. 스크립트 자신의 위치를 기준으로 data·references를 찾도록 한다.
4. Python 표준 라이브러리 외 의존성이 있는지 검증한다.
5. network·package install·임의 process 실행을 금지한다.
6. Windows와 POSIX에서 경로·UTF-8·줄바꿈을 검증한다.
7. upstream 제외 파일과 제외 이유를 provenance에 기록한다.

#### IO-005 — 디자인 시스템 산출물 계약

기본 동작:

- 대화창에 후보와 근거를 보고한다.
- 사용자 승인 없이 프로젝트 파일을 만들지 않는다.

명시적으로 저장할 때:

```text
.docs/design-system/{project-slug}/MASTER.md
.docs/design-system/{project-slug}/pages/{page-slug}.md
```

규칙:

1. 기존 파일이 있으면 diff를 제시하고 승인 전 덮어쓰지 않는다.
2. 화면별 override는 MASTER와 다른 값만 기록한다.
3. 색상 hex, token 이름, 숫자, 경로, 표는 문서 개선 단계의 보호 토큰으로 잠근다.
4. 저장 후 구조 검증을 수행한다.
5. 직접 호출이 최외곽 Markdown producer일 때 한 번만 `humanize-korean` 개선안을 제안한다.
6. 상위 producer 안에서 호출되면 child handoff를 억제한다.

#### TEST-003 — `ui-ux-pro-max` 단위·행동 검증

필수 fixture:

- SaaS dashboard 디자인 시스템 추천
- 공공·의료 화면의 접근성 우선 추천
- 기존 디자인 토큰이 있는 프로젝트에서 기존값 우선
- stack별 검색
- 검색 결과 0건과 잘못된 domain 처리
- project slug와 page slug 경로 탈출 차단
- 기존 MASTER 무승인 덮어쓰기 차단
- Markdown producer handoff 1회 보장
- Python command 후보 탐지
- Windows·POSIX 경로
- network 호출 없음

Codex·Claude smoke prompt:

- 디자인 방향만 요청
- design-system 저장 요청
- 기존 화면 UX 리뷰
- 프로토타입 handoff 요청
- 실제 화면 handoff 요청

### Phase 2 완료 기준

- [ ] 독립 호출이 가능하다.
- [ ] 원본 검색·데이터·참조 자산이 manifest로 닫혀 있다.
- [ ] Claude 전용 경로가 없다.
- [ ] 사용자 승인 없는 파일 생성·덮어쓰기가 없다.
- [ ] protected asset 검증과 eval이 통과한다.

---

## Phase 3. `motion-design` 독립 스킬 구현

### 목표

Motion Design의 전체 원본 지식 묶음을 보존하고, 하네스의 접근성·성능·저밀도 기본값을 적용한 플랫폼 중립 스킬을 만든다.

### 선행 승인

- upstream 선정 승인
- 일반 반영 승인
- director·patterns·reference·evals 추가에 대한 보호 자산 영향 승인

### 태스크

#### CORE-007 — 플랫폼 중립 `SKILL.md` 작성

대상:

- `skills/motion-design/SKILL.md`

계약:

1. 모션의 목적을 먼저 분류한다.
2. 정보 전달, 상태 변화, 공간 관계, 피드백, 브랜드 표현 중 무엇인지 밝힌다.
3. 정적 대안이 충분하면 모션을 생략한다.
4. 기존 제품의 모션 토큰과 컴포넌트를 먼저 조사한다.
5. timing, easing, property, choreography, repetition을 결정한다.
6. reduced-motion 대체안과 정지 상태를 함께 설계한다.
7. 구현 프레임워크를 임의로 바꾸지 않는다.
8. 실제 제품 구현은 `frontend-design`, 검증은 `impl-verify`로 공개 handoff한다.

#### IO-006 — 원본 지식 묶음 반입

대상:

- `skills/motion-design/director/**`
- `skills/motion-design/patterns/**`
- `skills/motion-design/reference/**`

작업:

1. upstream 파일을 원칙적으로 보존한다.
2. 수정한 파일은 modified로, 로컬 보완은 local-only로 기록한다.
3. 원본에 대한 번역·재구성·규칙 약화 지점을 semantic mapping에 기록한다.
4. 링크와 내부 참조가 plugin runtime에서도 해소되는지 검사한다.
5. 일부 파일을 제외할 경우 기능 영향과 이유를 승인 항목으로 분리한다.

#### IO-007 — 모션 명세 산출물 계약

기본 동작:

- 대화창에 모션 결정표와 구현·검증 기준을 보고한다.

명시적으로 저장할 때:

```text
.docs/design-system/{project-slug}/motion/{screen-or-component}.md
```

필수 항목:

- 목적
- trigger와 상태
- 대상 요소
- duration·delay·easing
- 사용할 속성
- 반복 조건
- reduced-motion 대체안
- 성능 위험
- 검증 기준

저장·덮어쓰기·humanize handoff는 `ui-ux-pro-max`와 같은 승인형 producer 계약을 따른다.

#### TEST-004 — `motion-design` 단위·행동 검증

필수 fixture:

- form loading → success → error
- modal entrance·exit
- dashboard 다중 요소 등장
- 엔터프라이즈 화면의 낮은 모션 밀도
- reduced-motion 대체안
- 모션이 불필요한 정적 화면에서 skip
- 과도한 ambient loop 차단
- layout-triggering 속성의 근거·성능 검증 요구
- 기존 제품 모션 토큰 우선
- 저장 경로 탈출과 무승인 덮어쓰기 차단

### Phase 3 완료 기준

- [ ] `director/`, `patterns/`, `reference/` 전체가 manifest로 닫혀 있다.
- [ ] 모션 강제 규칙이 로컬 안전 기준에 맞게 조정됐다.
- [ ] 접근성·성능·정적 대안이 필수 검토된다.
- [ ] Codex·Claude에서 같은 핵심 결과를 낸다.

---

## Phase 4. 기존 하네스 스킬 참고 반영

### 목표

신규 스킬을 독립적으로 쓸 수 있게 하면서 기존 디자인 흐름에서도 필요한 원칙과 handoff가 자연스럽게 연결되도록 한다.

### 태스크

#### CORE-008 — `design-prototype-docs` 보완

작업:

1. 디자인 시스템 존재 여부를 먼저 확인한다.
2. 필요 시 `ui-ux-pro-max` 결과를 입력으로 받는다.
3. 화면별 토큰, 상태, 반응형, 접근성, 빈 상태·오류 상태를 명세한다.
4. 모션이 필요한 후보와 목적만 식별하고 필요 시 `motion-design`으로 넘긴다.
5. 신규 스킬 내부 파일을 직접 읽도록 요구하지 않는다.

#### CORE-009 — `create-prototype` 보완

작업:

1. 승인된 디자인 시스템과 화면 명세를 사용한다.
2. 모션은 승인된 후보만 구현한다.
3. prototype 분기와 real-screen 분기의 경계를 출력에 명시한다.
4. `.docs/prototype/**` 산출물을 제품 코드로 복사하지 않는 규칙을 강화한다.
5. 사용자의 시각·UX 승인 결과를 구조화해 반환한다.

#### CORE-010 — `frontend-design` 보완

작업:

1. 기존 제품의 design system·component library·stack을 우선한다.
2. `ui-ux-pro-max` 결과는 설계 입력으로 사용하되 제품 코드 현실과 충돌하면 근거를 보고한다.
3. `motion-design` 명세가 있을 때만 해당 모션을 구현한다.
4. prototype 코드를 재사용하지 않고 승인된 결정만 재해석한다.
5. 접근성, responsive, reduced-motion, 성능 기준을 구현 완료 조건으로 둔다.

#### CORE-011 — `impl-verify` 보완

검증 매트릭스에 다음을 추가한다.

- 디자인 토큰 일관성
- 색 대비와 focus 표시
- keyboard·touch target
- viewport별 overflow·density
- loading·empty·error·success 상태
- reduced-motion
- 모션의 목적과 반복 조건
- 프레임 저하·layout thrashing 위험
- 프로토타입과 제품 source의 경계

#### IO-008 — provenance와 reference mapping 갱신

대상:

- `maintainer/upstreams/provenance/current-skills.json`
- 신규 source provenance
- `Docs/External_Skill_References.md`
- `Docs/Imported_Skill_Provenance.md`

규칙:

- 기존 스킬에 반영한 원칙을 upstream 파일·섹션 단위로 기록한다.
- 상당한 원문·표·체크리스트를 복사하지 않는다.
- 복사가 필요해지면 해당 파일은 `adapted`로 재분류하고 승인·NOTICE 영향을 다시 검토한다.

#### TEST-005 — 디자인 workflow 통합 fixture

시나리오:

1. 프로토타입만 요청
2. 처음부터 실제 화면 구현 요청
3. 프로토타입 승인 후 실제 화면 구현
4. 모션 없는 정적 화면
5. 모션이 있는 제품 화면
6. 기존 디자인 시스템이 있는 프로젝트
7. 디자인 시스템이 없는 신규 프로젝트

검증:

- 공개 skill-name handoff만 사용한다.
- child producer가 중복 humanize handoff를 만들지 않는다.
- prototype 코드가 제품 source에 복사되지 않는다.
- 실제 화면 구현에는 `frontend-design`이 적용된다.
- 양 분기 끝에 목적에 맞는 `impl-verify`가 수행된다.

### Phase 4 완료 기준

- [ ] 신규 독립 스킬과 기존 스킬의 역할이 중복되지 않는다.
- [ ] prototype·real-screen 분기가 동작 계약으로 고정됐다.
- [ ] reference 분류가 provenance와 실제 문구에 일치한다.

---

## Phase 5. Markdown 산출물·inventory·보호 자산 정합성

### 목표

신규 스킬이 선택적으로 만드는 Markdown을 기존 승인형 문서 개선 흐름에 안전하게 연결한다.

### 태스크

#### CORE-012 — Markdown producer inventory 확장

대상:

- `maintainer/inventory/markdown-artifact-flow.json`
- `maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py`
- `maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py`

작업:

1. `ui-ux-pro-max`를 조건부 Markdown producer로 등록한다.
2. `motion-design`을 조건부 Markdown producer로 등록한다.
3. producer 수와 이름을 JSON inventory에서 파생한다.
4. 하드코딩된 producer 배열을 제거하거나 inventory와 불일치하면 실패시킨다.
5. bundle fingerprint, outermost owner, child suppression, 승인 후 재검증 계약을 적용한다.

#### IO-009 — 보호 토큰과 구조 검증 정의

UI/UX 문서 보호 항목:

- hex·RGB·HSL
- CSS variable·design token
- font family·weight
- spacing·breakpoint
- stack·component 이름
- 표·코드 fence·경로·링크

Motion 문서 보호 항목:

- duration·delay
- easing curve
- property 이름
- trigger·state
- reduced-motion 조건
- 성능 budget

#### TEST-006 — producer 중복·변조 회귀검증

fixture:

- standalone 신규 스킬 저장
- 상위 workflow 내부 신규 스킬 호출
- 같은 bundle 재시도
- 일부 파일만 개선 승인
- 보호 토큰이 바뀐 개선안
- 개선 반영 뒤 원 producer 검증 실패

### Phase 5 완료 기준

- [ ] 신규 조건부 producer가 inventory에 반영됐다.
- [ ] 중복 개선 제안이 없다.
- [ ] 디자인·모션의 기계적 값이 문서 개선으로 변하지 않는다.

---

## Phase 6. 플러그인 패키징·라이선스·runtime 검증

### 목표

사용자 스킬 20종과 신규 upstream 자산을 Codex·Claude runtime에 결정적으로 패키징한다.

### 태스크

#### PKG-001 — capability와 skill count 갱신

작업:

1. `CAPABILITIES.json`의 논리 사용자 스킬에 신규 2종을 추가한다.
2. build·validator의 18 하드코딩을 20 또는 inventory 파생값으로 바꾼다.
3. 양 runtime의 skill 이름과 파일 hash를 비교한다.
4. runtime agent 0, alias 0을 유지한다.
5. 관리자 스킬 누출을 차단한다.

#### PKG-002 — runtime allowlist와 실행 자산 검증

작업:

1. UI 검색 스크립트 실행에 필요한 최소 권한만 명세한다.
2. 제한 없는 `Bash`를 frontmatter에서 사전 승인하지 않는다.
3. Python 실행 파일 탐지와 설치 누락 안내를 플랫폼 중립으로 만든다.
4. 스킬이 package manager로 Python을 자동 설치하지 않도록 한다.
5. Motion Design은 instruction/reference-only runtime임을 검증한다.

#### PKG-003 — LICENSE·NOTICE·lock closure

작업:

1. 두 직접 반입 source의 LICENSE를 plugin `licenses/`에 포함한다.
2. THIRD_PARTY_NOTICES에 원본, 고정 SHA, 수정 여부를 기록한다.
3. reference relationship은 copied package license 목록에 중복 생성하지 않는다.
4. `UPSTREAMS.lock.json`에는 packaged source와 실제 artifact hash를 닫는다.
5. 라이선스 hash 불일치 시 build를 실패시킨다.

#### PKG-004 — plugin 생성물 재생성

작업:

1. canonical `skills/**`에서 runtime을 생성한다.
2. archive와 checksum을 재생성한다.
3. 같은 source로 두 번 build해 tree manifest와 archive hash가 같은지 확인한다.
4. generated 파일을 직접 수정한 흔적이 없는지 확인한다.

#### TEST-007 — plugin 자동 검증

검증:

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/run_all_skill_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/freeze_manager_inventory.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/run_release_regression.py
git diff --check
```

### Phase 6 완료 기준

- [ ] 양 runtime에 같은 20개 사용자 스킬이 있다.
- [ ] UI/UX Pro Max의 data·scripts·references가 archive에 있다.
- [ ] Motion Design의 director·patterns·reference가 archive에 있다.
- [ ] LICENSE·NOTICE·lock이 닫혀 있다.
- [ ] plugin build가 결정적이다.

---

## Phase 7. README와 하네스 문서 최신화

### 목표

사용자와 관리자가 신규 디자인 흐름, 독립 스킬, 참고 관계, 별도 설치 대상을 혼동하지 않도록 문서를 갱신한다.

### 태스크

#### CORE-013 — `README.md` 갱신

반영 내용:

1. 사용자 스킬 18종을 20종으로 변경한다.
2. 스킬 목록에 `ui-ux-pro-max`, `motion-design`을 추가한다.
3. 일반 하네스 흐름은 기존 순서를 유지한다.
4. 별도 “디자인 작업 흐름”을 추가한다.
5. 프로토타입과 실제 화면 두 분기를 Mermaid로 표시한다.
6. prototype 코드 비승격 원칙을 명시한다.
7. 두 신규 스킬의 호출 예시를 Codex·Claude 형식으로 제공한다.
8. Caveman·Ruflo는 별도 설치 대상으로 설명하고 GitHub 링크를 건다.
9. 직접 반입형과 참고형의 차이를 짧게 설명한다.

#### CORE-014 — `Docs/Harness_Engineering_Intro.md` 갱신

중학생도 이해할 수 있는 수준으로 다음을 설명한다.

- UI/UX Pro Max: 화면의 색·글꼴·배치·사용 편의성을 정하는 “디자인 도서관과 검색 도구”
- Motion Design: 화면이 움직이는 이유·속도·순서를 정하는 “움직임 설계 가이드”
- 프로토타입: 버려도 되는 시험 화면
- 실제 화면: 제품 source에 구현되고 유지보수되는 화면
- 왜 prototype 코드를 그대로 제품에 넣지 않는지
- 모션을 항상 넣지 않는 이유
- Caveman과 Ruflo가 하네스에 포함되지 않는 이유

#### CORE-015 — `Docs/Harness_Engineering.md` 갱신

상세 반영:

1. 정본·책임 경계와 사용자 스킬 수 갱신
2. 일반 흐름과 디자인 전용 흐름의 관계
3. 두 갈래 분기의 입력·산출물·승인 gate·검증
4. 각 신규 스킬의 호출·skip 조건
5. 공개 skill-name handoff 계약
6. 디자인 시스템과 모션 명세의 선택적 저장 경로
7. Markdown producer·humanize handoff
8. direct/reference upstream 최신화 구조
9. Caveman·Ruflo 별도 설치 링크와 경계

#### CORE-016 — 연쇄 문서 갱신

대상:

- `Docs/README.md`
- `Docs/Plugin_Installation_Guide.md`
- `Docs/Imported_Skill_Provenance.md`
- `Docs/External_Skill_References.md`
- `Docs/Skill_Upstream_Update_Policy.md`
- `maintainer/README.md`
- 관련 `example/**`

규칙:

- 현재 문서에서 18종으로 고정된 표현을 20종으로 갱신한다.
- 과거 release evidence와 역사 계획의 숫자는 역사 기록으로 보존한다.
- 직접 반입과 참고 관계를 같은 것으로 설명하지 않는다.
- 별도 설치 도구가 이 플러그인의 필수 의존성인 것처럼 쓰지 않는다.

#### TEST-008 — 문서 검증

검증:

- 모든 로컬 Markdown 링크 확인
- Mermaid syntax 확인
- 현재 문서의 stale 18-skill 표현 검색
- 신규 스킬 이름·GitHub URL 검색
- Caveman·Ruflo가 runtime 포함 대상으로 표현되지 않았는지 검색
- prototype → product code 복사 금지 문구 확인
- Codex·Claude 호출 예시 확인

예상 검색:

```bash
rg -n "18종|18개|18 skills" README.md Docs maintainer/README.md
rg -n "ui-ux-pro-max|motion-design" README.md Docs maintainer
rg -n "JuliusBrussee/caveman|ruvnet/ruflo" README.md Docs
git diff --check
```

### Phase 7 완료 기준

- [ ] 세 핵심 문서에 디자인 전용 분기가 있다.
- [ ] 프로토타입과 실제 화면의 차이가 명확하다.
- [ ] 신규 스킬 호출·skip 조건을 찾을 수 있다.
- [ ] Caveman·Ruflo 링크와 별도 설치 경계가 있다.
- [ ] 현재 문서의 skill count가 일치한다.

---

## Phase 8. Codex·Claude CLI와 앱 실행 검증

### 목표

파일이 설치되는 것과 실제 모델이 스킬 계약을 수행하는 것을 구분해 네 실행 표면에서 검증한다.

### 태스크

#### TEST-009 — 자동 설치 smoke

검증:

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/smoke_cli_install.py
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py --check
```

확인:

- marketplace 등록
- plugin 설치
- cache에 20개 사용자 스킬
- 관리자 스킬 0개
- 두 신규 스킬의 전체 자산
- uninstall·cleanup

#### TEST-010 — Codex CLI 수동 행동 검증

예시:

```text
$ui-ux-pro-max
기존 React 관리자 화면의 디자인 시스템을 제안해줘.
현재 토큰이 있으면 우선하고 파일은 아직 만들지 마.
```

```text
$motion-design
이 결제 버튼의 loading → success → error 전환을 설계해줘.
reduced-motion 대체안과 성능 검증 기준도 포함해줘.
```

증적:

- 호출 인식
- references·data 사용 근거
- 무승인 쓰기 없음
- 공개 handoff
- 결과 캡처·버전·설치 경로

#### TEST-011 — Codex 앱 수동 행동 검증

시나리오:

- 신규 화면 디자인 방향
- 디자인 시스템 저장 승인·거절
- 프로토타입 분기
- 실제 화면 분기
- 모션 skip

#### TEST-012 — Claude Code CLI 수동 행동 검증

예시:

```text
/ai-agent-harness:ui-ux-pro-max
의료 예약 화면의 접근성 중심 디자인 시스템을 제안해줘.
```

```text
/ai-agent-harness:motion-design
모달 열기/닫기 동작을 설계하고 motion 감소 환경을 포함해줘.
```

#### TEST-013 — Claude 앱·Desktop Code 수동 행동 검증

지원되는 설치 표면에서 다음을 확인한다.

- 두 신규 스킬 목록 노출
- 명시 호출
- reference asset 접근
- prototype·real-screen routing
- 결과·버전·환경 증적

### Phase 8 판정 규칙

- 자동 설치 성공을 실제 모델 동작 성공으로 대신하지 않는다.
- CLI 성공을 앱 성공으로 대신하지 않는다.
- 지원되지 않는 앱 표면은 `SKIP`이 아니라 근거가 있는 `미지원`으로 기록한다.
- 네 표면의 수동 증적이 모두 충족되기 전에는 release-ready로 표시하지 않는다.

### Phase 8 완료 기준

- [ ] CLI 자동 설치 smoke가 통과했다.
- [ ] Codex CLI·앱 증적이 있다.
- [ ] Claude Code CLI·앱 증적이 있다.
- [ ] 두 신규 스킬의 직접 호출과 디자인 분기 흐름이 확인됐다.

---

## Phase 9. 최종 감사·릴리스 후보

### 목표

구현, upstream, plugin, 문서, 실제 실행 증적을 하나의 릴리스 후보로 닫는다.

### 태스크

#### TEST-014 — 전체 회귀검증

검증:

```bash
python maintainer/skills/skill-portfolio-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/run_all_skill_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/smoke_cli_install.py
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/freeze_manager_inventory.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/run_release_regression.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
git diff --check
```

#### TEST-015 — 의도 재감사

질문:

1. 두 신규 스킬은 독립 호출 가능한가?
2. 원본의 실행·참조 자산을 실제로 모두 패키징하는가?
3. direct/reference 관계가 같은 SHA를 가리키는가?
4. 기존 스킬은 외부 내부 경로에 결합되지 않았는가?
5. 디자인 전용 흐름이 일반 흐름을 불필요하게 복잡하게 만들지 않는가?
6. 프로토타입과 실제 제품 source 경계가 지켜지는가?
7. 모션을 필요 없는 화면에 강제하지 않는가?
8. 사용자 프로젝트에 local skill 디렉터리를 만들지 않는가?
9. Caveman·Ruflo가 별도 설치 대상으로만 설명되는가?
10. 문서·manifest·실제 runtime의 skill count가 모두 20인가?

#### PKG-005 — 릴리스 후보 갱신

작업:

1. semantic version을 변경 범위에 맞게 결정한다.
2. release metadata, archive, checksum, audit를 갱신한다.
3. packaged upstream SHA와 artifact hash를 기록한다.
4. 자동·수동 증적의 PASS·FAIL·미지원 상태를 구분한다.
5. unresolved FAIL이 있으면 release-ready를 차단한다.

### Phase 9 완료 기준

- [ ] 전체 자동 검증이 통과했다.
- [ ] 네 실행 표면의 판정이 기록됐다.
- [ ] upstream·license·NOTICE·lock이 닫혔다.
- [ ] 문서와 runtime이 같은 흐름과 수를 설명한다.
- [ ] release-ready 여부가 증적에 따라 결정됐다.

---

## 6. Phase 의존 관계

```mermaid
flowchart LR
    P0["Phase 0<br/>기준선·업스트림 확정"] --> P1["Phase 1<br/>거버넌스"]
    P1 --> P2["Phase 2<br/>UI/UX Pro Max"]
    P1 --> P3["Phase 3<br/>Motion Design"]
    P2 --> P4["Phase 4<br/>기존 스킬 참고 반영"]
    P3 --> P4
    P4 --> P5["Phase 5<br/>Markdown·inventory"]
    P5 --> P6["Phase 6<br/>플러그인 패키징"]
    P6 --> P7["Phase 7<br/>문서"]
    P7 --> P8["Phase 8<br/>CLI·앱 검증"]
    P8 --> P9["Phase 9<br/>최종 감사·릴리스"]
```

Phase 2와 Phase 3은 Phase 1 완료 후 서로 독립적으로 구현할 수 있다. 다만 이 저장소의 운영 방식에 따라 각 Phase를 구현·검증·커밋한 뒤 다음 Phase로 진행한다.

---

## 7. 구현 후 최종 상태

### 사용자 스킬 구성

| 영역 | 스킬 |
|---|---|
| 설치·기반 | `harness-setup`, `harness-bootstrap`, `git-scoped-account` |
| 설계·컨텍스트 | `design-doc`, `context-doc`, `doc-audit` |
| UI/UX 설계 | `ui-ux-pro-max`, `design-prototype-docs` |
| 모션 설계 | `motion-design` |
| 프로토타입 | `create-prototype` |
| 제품 UI | `frontend-design` |
| 구현 계획·점검 | `impl-doc`, `impl-fe-be-doc`, `impl-reuse-scan`, `impl-verify` |
| 품질·커밋 | `multi-review`, `pre-commit`, `commit`, `code-comment` |
| 문서 개선 | `humanize-korean` |

합계: 사용자 스킬 20종

### 관리자 스킬 구성

| 스킬 | 역할 |
|---|---|
| `custom-skill-design` | 신규·기존 스킬 구조와 행동 설계 |
| `skill-portfolio-maintainer` | 외부 upstream 탐색·분류·staging·승인·승격·rollback |
| `harness-plugin-maintainer` | Codex·Claude runtime 생성·검증·설치 시험·릴리스 |

관리자 스킬은 사용자 plugin payload에 포함하지 않는다.

---

## 8. 전체 완료 정의

- [ ] UI/UX Pro Max가 전체 실행 자산을 가진 독립 사용자 스킬로 동작한다.
- [ ] Motion Design이 전체 director·patterns·reference를 가진 독립 사용자 스킬로 동작한다.
- [ ] 두 스킬이 Codex·Claude에서 같은 논리 이름과 핵심 계약을 가진다.
- [ ] 두 upstream의 direct/reference 관계가 같은 고정 SHA로 관리된다.
- [ ] 기존 네 스킬에 필요한 원칙만 참고형으로 반영됐다.
- [ ] `README.md`, `Harness_Engineering_Intro.md`, `Harness_Engineering.md`에 디자인 전용 흐름이 있다.
- [ ] 디자인 흐름이 프로토타입과 실제 화면 두 갈래로 분기한다.
- [ ] prototype 코드는 제품 source로 승격되지 않는다.
- [ ] 모션은 조건부이며 접근성·성능·정적 대안을 검토한다.
- [ ] 사용자 스킬 수가 문서·inventory·plugin·runtime에서 20으로 일치한다.
- [ ] 사용자 프로젝트에 local skill 디렉터리를 생성하지 않는다.
- [ ] Caveman과 Ruflo는 GitHub 링크가 있는 별도 설치 대상으로만 설명된다.
- [ ] LICENSE·NOTICE·provenance·lock·protected asset 승인이 닫혔다.
- [ ] 자동 설치와 실제 Codex·Claude CLI·앱 행동 증적이 구분되어 기록됐다.
- [ ] 전체 회귀검증이 통과하고 unresolved FAIL이 없다.

