# UI/UX Pro Max v2.13.0 보호 자산 영향 보고서

| 항목 | 값 |
|---|---|
| 후보 ID | `ui-ux-pro-max-v2.13.0` |
| source ID | `ui-ux-pro-max-runtime`, `ui-ux-pro-max-principles` |
| 보호 범위 | `scripts/**`, `references/**`, `data/**`, `LICENSE*` |
| 검토 상태 | Phase 2 inventory 완료 / Phase 3 security·license 판정 대기 |

## 추가된 자산

| upstream 경로 | runtime preview 경로 | 처리 |
|---|---|---|
| `.claude/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py` | `skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py` | verbatim 추가 후보 |

## 수정된 자산

| upstream 경로 | runtime preview 경로 | 처리 |
|---|---|---|
| `.claude/skills/ui-ux-pro-max/scripts/design_system.py` | `skills/ui-ux-pro-max/scripts/design_system.py` | verbatim 수정 후보 |

변경은 dark-mode 의도·palette·anti-pattern 정합성을 계산하는 helper와 그 동작을
검증하는 test에 한정된다. 이 설명은 diff 관찰 결과일 뿐, Phase 3 security review 전의
채택 판단이 아니다.

## 변경 없는 보호 자산

- `data/**` 35개 파일: 변화 없음
- `references/**` 2개 파일: 변화 없음
- 기존 script 4개 파일: 변화 없음
- upstream `LICENSE`: v2.11.3과 v2.13.0 사이 변화 없음

## 삭제·이동·교체

없음. `destructive_changes=[]`이며 G5 파괴적 변경 승인은 요구하지 않는다.

## 주의 항목

- `LICENSE` SHA-256은 raw archive 기준 기존 accepted provenance와 일치한다. Windows
  `core.autocrlf`가 켜진 작업본 hash를 raw upstream evidence로 사용하지 않는다.
- runtime preview의 local `SKILL.md`와 `evals/run_evals.py`는 upstream 반입물이 아니며
  유지 대상이다.
- reference-only 관계는 upstream 파일을 복사하지 않는다.

## 승인 상태

- 일반 승인 ID: 미발급
- 자산 영향 승인 ID: 미발급
- 파괴적 변경 승인 ID: 해당 없음

Phase 3에서 license/security 검토가 통과하고 실제 보호 자산 반입을 결정할 때에만
자산 영향 승인을 별도 요청한다.
