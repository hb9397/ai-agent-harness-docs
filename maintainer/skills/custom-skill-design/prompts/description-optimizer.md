# prompts/description-optimizer.md
# 역할: SKILL.md description 필드 트리거 최적화 상세 절차

---

## 라우팅 표

| 환경 | 읽을 섹션 |
|------|----------|
| Claude Code | [쿼리 생성] + [사용자 검토] + [자동 최적화] + [적용] |
| Claude.ai | [쿼리 생성] + [수동 개선] + [적용] |

---

## 트리거 메커니즘 이해

`description` 필드는 Claude가 스킬을 호출할지 결정하는 **유일한** 기준이다.
Claude는 스스로 처리할 수 있는 단순한 단일 단계 작업에는 스킬을 호출하지 않는다.
복잡하거나 다단계이거나 전문화된 요청에서만 description이 일치할 때 스킬이 호출된다.

→ 테스트 쿼리는 충분히 구체적이고 복잡해야 한다.
→ "PDF 읽어줘" 같은 단순 요청은 description이 완벽해도 스킬을 호출하지 않는다.

---

## [쿼리 생성] — 환경 무관

### 목표: should-trigger 10개 + should-not-trigger 10개

**should-trigger 쿼리 작성 기준 (8-10개)**
- 같은 의도를 다양한 표현으로 (격식체/구어체 혼합)
- 스킬 이름을 명시하지 않아도 명백히 이 스킬이 필요한 케이스
- 흔치 않은 엣지 케이스
- 유사 스킬과 경쟁하지만 이 스킬이 이겨야 하는 케이스

**should-not-trigger 쿼리 작성 기준 (8-10개)**
- 키워드는 겹치지만 실제로는 다른 스킬이 필요한 케이스 (핵심)
- 이 스킬이 하는 일의 일부만 필요한 케이스
- 도메인은 같지만 다른 도구가 더 적합한 케이스
- 너무 단순해서 스킬 없이 처리 가능한 케이스

**나쁜 예 (피할 것)**
```
"코드 리뷰해줘"            ← 너무 단순, 스킬 자체가 호출 안 됨
"피보나치 함수 짜줘"        ← 관련 없는 것을 negative로 쓰면 테스트 의미 없음
```

**좋은 예 (지향할 것)**
```
should-trigger:
"우리 팀 코드 리뷰 프로세스가 너무 제각각인데, PR마다 체크해야 할 항목을
자동으로 분석해주는 스킬을 Claude Code에 만들고 싶어.
보안, 성능, 가독성 세 관점에서 체크해줬으면 해"

should-not-trigger:
"방금 작성한 PR 설명 좀 다듬어줘. 변경사항이 뭔지 명확하게 써야 하는데
지금 너무 길고 산만한 것 같아"  ← 문서 편집, 스킬 설계 아님
```

저장 형식:
```json
[
  {"query": "쿼리 내용", "should_trigger": true},
  {"query": "쿼리 내용", "should_trigger": false}
]
```

---

## [사용자 검토]

쿼리를 사용자에게 공유해 검토를 요청한다:
> "트리거 테스트 쿼리 20개를 만들었습니다. 추가·수정·삭제할 것이 있으면 알려주세요.
> should-trigger가 맞는지, should-not-trigger 케이스가 충분히 까다로운지 특히 확인 부탁드립니다."

사용자 승인 후 진행한다.

---

## [자동 최적화] — Claude Code 전용

```bash
python -m scripts.run_loop \
  --eval-set {eval-set-path} \
  --skill-path {skill-path} \
  --model {현재 세션 모델 ID} \
  --max-iterations 5 \
  --verbose
```

**실행 중 진행상황을 주기적으로 사용자에게 알린다:**
> "현재 iteration 3/5 진행 중. 현재 점수: train 0.82 / test 0.79"

**최적화 로직 (스크립트 내부)**:
- eval set을 train 60% / test 40%로 분할
- 각 쿼리를 3회 실행해 트리거율 측정
- 실패 패턴 기반으로 새 description 제안 (extended thinking)
- train + test 점수 기준으로 최적 description 선택 (overfitting 방지)
- 최대 5회 반복

결과에서 `best_description`을 추출해 [적용] 단계로 진행한다.

---

## [수동 개선] — Claude.ai 환경

자동화 스크립트 없이 다음 방법으로 개선한다:

1. 생성한 should-trigger 쿼리들을 직접 시뮬레이션해 현재 description으로 트리거 여부를 판단
2. 놓치는 케이스 패턴을 파악해 description에 해당 맥락·키워드를 추가
3. 잘못 트리거되는 케이스를 파악해 description의 범위를 좁힘
4. 개선된 description을 2-3가지 후보로 제안해 사용자가 선택

---

## [적용]

최적 description을 SKILL.md frontmatter에 적용한다:

```bash
# 기존 description 백업 후 교체
head -5 SKILL.md  # 현재 내용 확인
```

사용자에게 before/after를 보여준다:
```
## Description 업데이트

[이전]
"..."

[이후]
"..."

트리거 정확도: {이전 점수} → {이후 점수}
```
