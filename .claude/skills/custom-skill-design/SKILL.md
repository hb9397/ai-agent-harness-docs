---
name: custom-skill-design
description: "관리자가 사용자용 또는 관리자용 AI Agent Skill을 설계·생성·테스트·고도화할 때 사용한다. '스킬 만들어줘', '스킬 설계', '스킬 개선', 'SKILL.md 작성', '워크플로우를 스킬로', '스킬 테스트', '스킬 트리거 최적화' 요청을 사용자/관리자 정본 경계와 Codex·Claude 실행 표면에 맞게 처리한다."
allowed-tools: Read, Write, Glob, Grep
---

## 스킬 연계

```
사용자 요청 (자연어 / 기존 워크플로우 / 기존 스킬 파일)
    ↓
custom-skill-design  ← 지금 여기
    ↓
생성된 스킬 디렉토리 (SKILL.md + 필요한 보조 자산만)
    ↓  ← eval 루프로 품질 검증
    ↓  ← description 최적화로 트리거 정확도 향상
    ↓
Codex CLI/App / Claude Code/Desktop Code에서 사용 가능한 완성 스킬
```

---

# Skill Designer

인터뷰 → 설계 → 초안 생성 → **테스트 & 반복 개선** → description 최적화까지
스킬 생애주기 전체를 한 흐름으로 진행한다.

설계 원칙은 `prompts/design-principles.md`에, 테스트·개선 로직은 `prompts/eval-loop.md`에 있다.
이 파일에 원칙을 반복하지 않는다.

> **유연성 원칙**: 사용자가 "그냥 빠르게 만들어줘" 하면 eval 루프를 생략해도 된다.
> 사용자가 있는 단계에서 바로 합류한다.

---

## 진입 분기

| 상황 | 이동할 Step |
|------|------------|
| "스킬 새로 만들어줘" / 아이디어만 | Step 1-A → 2 → 3 → 4 → 5 → 6 |
| 기존 워크플로우 → 스킬 전환 | Step 1-B → 2 → 3 → 4 → 5 → 6 |
| 기존 SKILL.md 고도화 | Step 1-C → 4 → 5 → 6 |
| 구조 점검만 | Step 4 (보고만, 파일 수정 없음) |
| eval / 테스트만 실행 | Step 5 |
| description 트리거 최적화만 | Step 6 |

---

## Step 1 — 진입 유형 감지 및 초기 인터뷰

추론 우선, 질문은 최소화한다. 사용자 기술 수준에 맞게 용어를 조절한다.
세부 질문 우선순위는 `prompts/interview.md`의 [신규] 섹션 참조.

**1-A. 신규 스킬 설계**
→ `prompts/interview.md`의 [신규] 섹션으로 인터뷰 진행.

**1-B. 기존 워크플로우 → 스킬 전환**
대화 히스토리에서 자동 추출한다:
- 사용한 도구 목록 / 단계별 순서 / 사용자가 수정 요청한 지점 / 입출력 형식

추출 후 확인 게이트:
> "위 내용을 기반으로 스킬을 설계할까요? 빠진 게 있으면 알려주세요."

**1-C. 기존 스킬 고도화**
`Read`로 `[경로]/SKILL.md`의 frontmatter와 워크플로를 확인하고, `Glob`으로
`[경로]/prompts/**`, `[경로]/templates/**`, `[경로]/references/**`,
`[경로]/scripts/**`, `[경로]/evals/**`의 실제 파일 목록을 확인한다. 플랫폼 전용
shell 구문으로 존재 여부를 추측하지 않는다.
→ 구조 파악 후 Step 4(검증)으로 이동.

---

## Step 2 — 스킬 범위 확정

`prompts/interview.md`의 [범위 확정] 섹션을 참조한다.

이 Step의 출력 (대화창 출력, 파일 생성 안 함):
```
## 스킬 설계 요약
- 스킬명:
- 핵심 목적:
- 트리거 상황 (3가지 이상):
- 입력 / 출력:
- 필요 도구:
- 지침 자유도: 높음 / 중간 / 낮음
  (창의적·가변 작업은 높게, 실패 비용이 큰 취약 절차는 낮게)
- 보조 자산 계획: 없음 / scripts / references / assets / prompts / templates
- 대상 플랫폼 메타데이터: 공통만 / Codex `agents/openai.yaml` 추가
- 테스트 케이스 필요 여부: Yes / No
  (출력이 객관적으로 검증 가능하면 Yes 권장)
- 병렬 처리 여부:
- 연계 스킬:
- 산출물/적용범위 → C-1 확인 단계 필요 여부: Yes / No
  (파일 생성·코드 수정 등 프로젝트 구조에 의존하면 Yes)
```

확인 게이트:
> "위 설계 요약이 맞나요? (확인 / 수정)"

---

## Step 3 — 스킬 파일 초안 생성

**승인 후에만** 파일을 생성한다.

### 3-1. 파일 구성 결정

| 조건 | 생성할 파일 |
|------|------------|
| 규칙이 단순 (Step ≤ 3) | SKILL.md 단독 |
| 인터뷰·분석 로직이 복잡 | + prompts/interview.md |
| 출력 양식 고정 | + templates/output.md |
| 독립 관점 3개 이상 | + prompts/[관점별].md |
| 반복되는 결정론적 작업 | + scripts/[도구].py 또는 플랫폼 중립 스크립트 |
| 필요할 때만 읽을 상세 지식 | + references/[주제].md |
| 결과물에 복사·사용할 파일 | + assets/[파일] |
| Codex UI 메타데이터가 실제로 필요 | + agents/openai.yaml |
| 복합 구조 | SKILL.md + 승인된 보조 자산만 |

파일 구성·작성 규칙은 `prompts/design-principles.md` 참조.

### 스킬 간 연결 규칙

한 스킬이 다른 스킬의 결과를 필요로 할 때는 **공개 skill 이름으로만** 연결한다.

- 상대방 스킬의 내부 파일, 상대경로, 구현 세부사항에 결합하지 않는다.
- 상대방의 `references/`, `data/`, `scripts/` 경로를 직접 읽도록 요구하지 않는다.
- 같은 플러그인 안에서 공개 이름으로 수행하는 승인형 workflow handoff는 허용한다.
- 상대방이 아직 없거나 이름이 바뀔 수 있으면 handoff를 선택적 제안으로 둔다.

내부 경로에 결합하면 상대 스킬의 리팩터링이 이쪽을 조용히 깨뜨리고, 두 스킬을
독립적으로 배포하거나 교체할 수 없게 된다.

Codex의 공개 `$skill-creator` 또는 플랫폼 기본 validator가 현재 환경에 제공되면 그
공개 계약을 **보조 검사**로 사용할 수 있다. 로컬 설치 절대경로나 해당 스킬 내부
스크립트 경로를 하드코딩하지 않는다. Claude에서도 같은 핵심 스킬이 작동하도록
공통 자체 체크리스트와 eval을 항상 기준으로 유지한다.

### 3-2. 저장 경로 결정

파일을 만들기 전에 먼저 배포 대상을 분류한다.

| 대상 | 관리 저장소 안의 정본 |
|------|----------------------|
| 사용자 플러그인에 배포할 스킬 | `skills/{skill-name}/` |
| 관리자만 이 저장소에서 사용할 스킬 | `maintainer/skills/{skill-name}/` |

- 관리 저장소 밖에서 작업하는 경우에는 사용자가 명시한 현재 프로젝트 경로만 사용한다.
- `./{skill-name}` 같은 저장소 루트 임시 정본은 만들지 않는다.
- 사용자용인지 관리자용인지 불명확하면 파일 생성 전에 한 번 확인한다.
- 정본 분류와 대상 경로를 Step 2 설계 요약에 포함하고 승인받는다.

### 3-3. 테스트 케이스 초안 (Step 2에서 Yes면 바로 작성)

2-3개의 현실적인 테스트 프롬프트를 작성해 사용자에게 공유한다:
> "아래 테스트 케이스로 스킬을 검증하려 합니다. 추가하거나 수정할 내용이 있나요?"

`evals/evals.json`에 저장 (assertions는 아직 비워둠):
```json
{
  "skill_name": "{skill-name}",
  "evals": [
    {
      "id": 1,
      "prompt": "실제 사용자가 입력할 법한 구체적인 요청",
      "expected_output": "기대 결과 설명",
      "files": []
    }
  ]
}
```

---

## Step 4 — 설계 검증 (구조 체크리스트)

`prompts/checklist.md`를 참조해 점검한다.

출력 형식:
```
## 검증 결과
✅ 통과 (N개)
⚠️  보완 필요:
  - [항목]: [이유] → [권장 수정 방향]
```

- `구조 점검만` 진입이면 보완 필요 항목과 근거만 보고하고 파일을 수정하지 않는다.
- 생성·개선 요청이면 사용자가 승인한 범위 안에서만 보완하고 재점검한다.
- 보호 자산의 삭제·이동·교체는 이 단계에서 자동 수행하지 않는다.
- 전체 통과 후 Step 5로 이동한다.

---

## Step 5 — 테스트 실행 & 반복 개선 루프

세부 절차는 `prompts/eval-loop.md` 참조.

### 개요 흐름

```
테스트 케이스 실행
    ↓
assertions 초안 작성 (실행 중 병행)
    ↓
결과 평가 (정성 + 정량)
    ↓
사용자 피드백 수집
    ↓
스킬 개선
    ↓
반복 (만족할 때까지)
```

### 환경별 실행 방식

| 환경 | 방식 |
|------|------|
| Codex CLI/App | 별도 task에서 with-skill / baseline 실행, 파일·트리거 결과 기록 |
| Claude Code/Desktop Code | with-skill / baseline 실행, 지원 시 sub-agent 병렬화 |
| Claude.ai | 순차 실행, 결과를 대화창에 직접 출력 |
| Cowork | `eval-loop.md`의 [Cowork] 섹션 참조 |

### 개선 루프 종료 조건

- 사용자가 만족을 표시
- 피드백이 모두 비어 있음 (전부 양호)
- 더 이상 의미 있는 개선이 없음

---

## Step 6 — Description 트리거 최적화

스킬이 "언제 호출되는가"를 결정하는 description 필드를 최적화한다.
세부 절차는 `prompts/description-optimizer.md` 참조.

### 개요

1. should-trigger / should-not-trigger 쿼리 20개 생성
2. 사용자 검토 및 수정
3. Codex·Claude에서 격리된 trigger matrix 실행
4. 최적 description을 SKILL.md frontmatter에 적용

### 환경별 가용성

| 환경 | 가용 여부 |
|------|----------|
| Codex CLI/App | 수동 trigger matrix 또는 관리자가 별도로 제공한 runner |
| Claude Code/Desktop Code | 수동 trigger matrix 또는 관리자가 별도로 제공한 runner |
| Claude.ai | 수동으로 description 개선 제안만 |

이 스킬 번들에는 description 자동 최적화 runner가 포함되어 있지 않다. 존재하지 않는
`scripts.run_loop`를 호출하지 않으며, runner를 별도로 도입하려면 출처·권한·eval을
검증한 뒤 보호 자산 승인 절차를 거친다.

---

## Step 7 — 관리자 정본 저장·projection 확인 (CS-4)

현재 작업 위치가 원본 하네스 관리 레포(`ai-agent-harness-docs` 등) **밖**인 경우, 생성/수정한 관리자 스킬을 관리 레포에도 반영할지 사용자에게 확인한다.

> "스킬이 원본 하네스 관리 레포 밖에서 생성/수정되었습니다.
> 관리 레포의 관리자 정본(`{정본경로}/maintainer/skills/{skill-name}/`)에도 반영할까요? (승인 / 나중에 / 취소)"

- 승인 시: 관리 레포의 `maintainer/skills/{skill-name}/` 디렉토리에 복사·갱신한다.
- 나중에 / 취소 시: 현재 위치에만 저장하고 안내한다.
- 원본 하네스 관리 레포 경로를 모르면 사용자에게 묻는다.

현재 위치가 원본 하네스 관리 레포 내부이면
`maintainer/skills/{skill-name}/`가 정본인지 확인한다. projection 갱신이 필요하면
`harness-plugin-maintainer`를 명시 호출해 **관리자 projection 동기화와 check만**
요청한다. 다른 관리자 스킬의 내부 스크립트 경로를 직접 호출하지 않는다.

---

## Step 8 — 최종 패키징 및 사용 안내 (CS-5)

대화창에 출력:

```
## 완성된 스킬: {skill-name}

파일 구조:
{skill-name}/
├── SKILL.md
├── prompts/ 또는 references/     # 필요한 경우만
├── templates/ 또는 assets/       # 필요한 경우만
├── scripts/                      # 결정론적 반복 작업이 있는 경우만
├── agents/openai.yaml            # Codex UI 메타데이터가 필요한 경우만
└── evals/evals.json

배포 방법:
  1. 관리자용 스킬이면 원본 하네스 관리 레포의 maintainer/skills/{skill-name}/ 에 저장한 뒤
     harness-plugin-maintainer를 명시 호출해 .agents/.claude repo-local projection을 갱신·검증
  2. 사용자용 스킬이면 사용자 플러그인 원본 skills/{skill-name}/ 에 저장한 뒤
     harness-plugin-maintainer의 플러그인 생성 흐름으로 배포

트리거 예시 문장:
  - "{trigger-1}"
  - "{trigger-2}"
  - "{trigger-3}"

다음 단계 제안:
  - 테스트 케이스 추가 및 재검증
  - Description 트리거 최적화 (Step 6)
  - 연계 스킬과의 통합 테스트
  - harness-plugin-maintainer로 사용자 플러그인 재빌드·검증
```

## 출처 및 변경 고지

이 관리자용 스킬은
[`anthropics/skills`의 `skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
내용을 한국어로 번역하고 이 하네스의 인터뷰, 거버넌스, projection, 테스트, 플러그인 릴리스
경계에 맞게 크게 재구성한 수정 파생물이다. 원본은 Apache License 2.0으로 배포된다.
적용한 커밋과 파일 대응표는
`maintainer/upstreams/provenance/anthropic-skills/`에서 관리한다.

또한
[`openai/codex`의 공식 `skill-creator`](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md)
에서 간결성, 작업별 지침 자유도, 점진적 공개, 보조 자산 역할, 검증 무결성,
Codex용 `agents/openai.yaml` 관리 원칙을 **참조 전용**으로 사용한다. OpenAI 원본
파일·스크립트는 이 스킬에 복사하지 않으며, 해당 관계는 `reference`로 추적한다.

## 검증

```bash
python maintainer/skills/custom-skill-design/evals/run_evals.py
```
