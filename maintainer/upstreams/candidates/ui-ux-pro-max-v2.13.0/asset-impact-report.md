# UI/UX Pro Max v2.13.0 보호 자산 영향 보고서

| 항목 | 값 |
|---|---|
| 후보 ID | `ui-ux-pro-max-v2.13.0` |
| source ID | `ui-ux-pro-max-runtime`, `ui-ux-pro-max-principles` |
| 보호 범위 | `scripts/**`, `references/**`, `data/**`, `LICENSE*` |
| 검토 상태 | Phase 3 license·security 판정 통과 / G4 자산 영향 승인 대기 |

## 추가된 자산

| upstream 경로 | runtime preview 경로 | 처리 |
|---|---|---|
| `.claude/skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py` | `skills/ui-ux-pro-max/scripts/tests/test_design_system_mode.py` | verbatim 추가 후보 |

## 수정된 자산

| upstream 경로 | runtime preview 경로 | 처리 |
|---|---|---|
| `.claude/skills/ui-ux-pro-max/scripts/design_system.py` | `skills/ui-ux-pro-max/scripts/design_system.py` | verbatim 수정 후보 |

변경은 dark-mode 의도·palette·anti-pattern 정합성을 계산하는 helper와 그 동작을
검증하는 test에 한정된다. Phase 3 정적 검토에서 변경분은 Python 표준 라이브러리·local
module만 사용하며 network, subprocess, shell, dynamic execution을 추가하지 않는 것으로
확인했다.

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
- `design_system.py`의 기존 `persist_design_system()`은 `--output-dir`에 문서를 쓰는
  기능이다. runtime preview의 local `SKILL.md`는 명시적 사용자 요청, 프로젝트 `.docs/`
  경로, 기존 내용 확인을 요구하므로, 이번 diff가 새 write path나 무승인 저장을 만들지
  않는다.
- static 검사와 runtime preview의 `python -m unittest discover -s scripts/tests -v` 실행
  결과는 36 passed다. 수정은 dark-mode 선택 결과에만 영향을 줄 수 있으며, 새 test가 그
  회귀 경계를 고정한다.

## 승인 상태

- G2 license/security: 통과
- G3 일반 적용 승인 ID: promotion handoff 전까지 미발급
- G4 자산 영향 승인 ID: 보호 script/test 2개 반입 전 명시적으로 발급 필요
- G5 파괴적 변경 승인 ID: 해당 없음

따라서 후보 판정은 `accept-for-staging`이다. stage와 dry-run은 canonical을 건드리지
않지만, 실제 promotion은 G4 자산 영향 승인 ID 없이는 진행할 수 없다.
