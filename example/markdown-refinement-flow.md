# Markdown refinement flow 예시

이 예시는 `.md` 산출물을 만드는 스킬 뒤에 `humanize-korean`을 사용하는 최소 흐름을 보여준다. 전체 원문을 중복 복제하지 않고, 변경 검토 방식만 보여준다.

---

## 1. 원 producer 산출물

예: `impl-doc`이 다음 파일을 생성했다.

```text
.docs/impl-doc/lhb9397/260729-1.selector-recovery-impl-doc.md
```

원 producer 검증 결과:

| 항목 | 결과 |
|------|------|
| 필수 섹션 | PASS |
| roadmap index 링크 | PASS |
| 참조 경로 | PASS |
| 코드블록 fence | PASS |

---

## 2. `humanize-korean` 개선안 요청

```text
humanize-korean document-refinement profile로 위 Markdown을 개선안만 제시해줘.
원본 파일은 수정하지 말고, 보호 token과 링크·표·코드블록을 보존해줘.
```

---

## 3. 개선안 요약

| 영역 | 제안 | 이유 |
|------|------|------|
| 개요 문단 | 반복 표현 축약 | 첫 화면에서 목적을 빠르게 파악 |
| 검증 섹션 | PASS 조건 문장 정리 | 구현자가 완료 기준을 덜 오해함 |
| 주의사항 | 금지/대안 구조로 재배치 | 실행 중 판단 비용 감소 |

보호 token 검사:

| Token | 결과 |
|-------|------|
| `.docs/impl-doc/lhb9397/260729-1.selector-recovery-impl-doc.md` | preserved |
| `AGENTS.md` | preserved |
| `MAX_RECOVERY_ATTEMPTS` | preserved |
| 코드블록 fence | preserved |

---

## 4. 사용자 승인 diff 예시

```diff
- 이 단계에서는 셀렉터 복구 로직을 구현한다.
+ 이 단계의 목표는 셀렉터 복구 로직을 구현하고, 실패 시 사람이 판단할 수 있는 상태로 중단하는 것이다.
```

사용자가 승인하지 않으면 원본 파일은 그대로 둔다.

사용자가 승인하면 승인된 변경만 반영한다.

---

## 5. 재검증

승인 반영 후 원 producer가 다시 확인한다.

| 항목 | 결과 |
|------|------|
| 문서 구조 | PASS |
| 링크·index | PASS |
| bridge 영향 | PASS |
| downstream 입력 가능 | PASS |

최종적으로 downstream 구현·검증 스킬은 승인된 최종 Markdown만 입력으로 사용한다.
