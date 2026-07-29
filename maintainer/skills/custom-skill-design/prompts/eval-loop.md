# prompts/eval-loop.md
# 역할: 테스트 케이스 실행, 결과 평가, 반복 개선 루프 상세 절차

---

## 라우팅 표

| 환경 | 읽을 섹션 |
|------|----------|
| Claude Code (sub-agent 가능) | [병렬 실행] + [평가] + [개선] |
| Claude.ai | [순차 실행] + [평가] + [개선] |
| Cowork / headless | [Cowork] + [평가] + [개선] |

---

## [병렬 실행] Claude Code 환경

### 워크스페이스 구조

```
{skill-name}-workspace/
└── iteration-1/
    ├── eval-{설명적이름}/
    │   ├── with_skill/outputs/
    │   ├── baseline/outputs/      ← 신규 스킬: without_skill / 개선: 구버전
    │   ├── eval_metadata.json
    │   └── timing.json
    └── benchmark.json
```

디렉토리는 실행하면서 생성한다. 미리 전체를 만들지 않는다.

### 실행 순서

**같은 턴에** with-skill과 baseline을 동시에 spawn한다. 순서를 나눠서 내지 않는다.

with-skill 프롬프트:
```
Skill path: {skill-path}
Task: {eval prompt}
Input files: {파일 목록 또는 "none"}
Save outputs to: {workspace}/iteration-N/eval-{name}/with_skill/outputs/
```

baseline 프롬프트:
```
Task: {eval prompt}  ← 스킬 없이, 동일 프롬프트
Input files: {파일 목록 또는 "none"}
Save outputs to: {workspace}/iteration-N/eval-{name}/baseline/outputs/
```

각 eval 디렉토리에 `eval_metadata.json` 생성 (assertions는 실행 중 작성):
```json
{
  "eval_id": 0,
  "eval_name": "기능을-설명하는-이름",
  "prompt": "테스트 프롬프트",
  "assertions": []
}
```

### 타이밍 데이터 캡처

subagent 완료 알림에서 `total_tokens`와 `duration_ms`를 즉시 저장한다.
이 데이터는 알림 외에 다시 얻을 수 없다.

```json
{
  "total_tokens": 0,
  "duration_ms": 0,
  "total_duration_seconds": 0
}
```

---

## [순차 실행] Claude.ai 환경

sub-agent가 없으므로 직접 순차로 실행한다.
자신이 스킬을 작성했기 때문에 완전한 독립성은 없지만, 동작 확인으로는 충분하다.

1. `SKILL.md`를 읽고 해당 스킬의 지침을 따라 테스트 프롬프트를 직접 수행한다.
2. 결과를 대화창에 직접 출력한다.
3. 파일 출력물(docx, xlsx 등)은 파일로 저장하고 경로를 사용자에게 안내한다.
4. 사용자에게 바로 피드백을 요청한다:
   > "이 결과가 어떤가요? 수정할 부분이 있으면 알려주세요."

baseline 비교는 생략한다. 정량 벤치마크도 생략한다.
**Description 최적화(Step 6)는 Claude.ai에서 수동 제안만 가능하다.**

---

## [Cowork]

- sub-agent 있음 → 병렬 실행 가능
- 브라우저 없음 → eval 뷰어 실행 시 `--static {output_path}` 옵션 사용
- 사용자가 "Submit All Reviews" 클릭 시 `feedback.json` 다운로드 → workspace에 복사
- Description 최적화 스크립트 (`run_loop.py`) 사용 가능

---

## [평가] 실행 중 병행 작업 — assertions 초안 작성

실행이 진행되는 동안 기다리지 말고 assertions를 작성한다.

### 좋은 assertions 기준

- **객관적으로 검증 가능**해야 한다 (사람이 판단해야 하는 것은 정성 평가로)
- **이름이 서술적**이어야 한다 (뷰어에서 한눈에 무엇을 검사하는지 알 수 있게)
- 프로그래밍으로 검증할 수 있으면 스크립트로 작성한다 (더 빠르고 재현 가능)

### assertions 필드 형식

`eval_metadata.json`과 `evals/evals.json`에 추가:
```json
"assertions": [
  {
    "text": "출력 파일이 존재하는가",
    "passed": null,
    "evidence": ""
  }
]
```

그레이딩 후 `grading.json`에 결과 저장:
```json
{
  "expectations": [
    {
      "text": "출력 파일이 존재하는가",
      "passed": true,
      "evidence": "output.docx가 with_skill/outputs/ 에 존재함"
    }
  ]
}
```

> **주의**: 필드명은 반드시 `text`, `passed`, `evidence`를 사용한다.
> `name`/`met`/`details` 등 다른 변형은 뷰어가 인식하지 못한다.

---

## [개선] 스킬 개선 원칙

피드백을 받은 후 스킬을 개선할 때 아래 원칙을 따른다.

### 1. 구체 사례에서 일반 원칙으로

테스트 케이스 2-3개에만 딱 맞게 고치는 것이 목표가 아니다.
수백만 번 다른 입력에 쓰일 스킬을 만드는 것이 목표다.
피드백의 근본 원인을 파악해 일반화된 지침으로 녹인다.

### 2. 간결하게 유지

효과 없는 내용을 제거한다.
트랜스크립트를 직접 읽어서 모델이 시간을 낭비하는 부분을 찾는다.
그 부분을 유발하는 지침을 삭제하거나 재작성한다.

### 3. MUST 대신 WHY

`ALWAYS`, `NEVER`, `MUST`를 남발하지 말고 이유를 설명한다.
이유를 아는 모델이 새로운 상황에서 더 잘 판단한다.

### 4. 반복 패턴 → scripts/로 이동

3개 이상의 테스트 케이스에서 같은 헬퍼 스크립트를 반복 작성하면
`scripts/` 디렉토리에 한 번만 작성하고 스킬에서 참조하게 한다.

### 반복 루프

```
개선 적용 → 새 iteration-N/ 디렉토리에서 재실행
→ 뷰어 실행 (--previous-workspace 로 이전 결과 비교)
→ 피드백 수집 → 개선
```

종료: 사용자 만족 / 피드백 모두 빈칸 / 더 이상 개선 없음
