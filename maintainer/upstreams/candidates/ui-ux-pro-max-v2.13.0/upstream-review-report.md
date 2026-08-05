# UI/UX Pro Max v2.13.0 업스트림 검토 보고서

| 항목 | 값 |
|---|---|
| 후보 ID | `ui-ux-pro-max-v2.13.0` |
| 관계 그룹 | `ui-ux-pro-max` |
| 대상 source | `ui-ux-pro-max-runtime` (adapted), `ui-ux-pro-max-principles` (reference) |
| baseline | `v2.11.3` / `4857a2c5ef989794751a0f66b8545a4a49566286` |
| candidate | `v2.13.0` / `4d140cf8ff6842de13213c7214eff3810371beb2` |
| 확인일 | 2026-08-05 |

## 후보 범위

`source-tree/`에는 exact target commit의 generated
`.claude/skills/ui-ux-pro-max/` tree 44개 파일과 `LICENSE`를 Git archive 원본
bytes로 보관한다. `runtime-preview/`는 현재 canonical skill의 local contract와
local eval을 유지한 채, 변경된 verbatim script 1개와 추가된 test 1개를 반영한
예상 tree다. canonical `skills/`, lock, plugin runtime은 이 Phase에서 변경하지 않았다.

## 3-way 비교 결과

| 비교 | 결과 | 증적 |
|---|---|---|
| upstream `v2.11.3..v2.13.0` | `scripts/design_system.py` 수정, `scripts/tests/test_design_system_mode.py` 추가; 그 외 generated skill과 LICENSE 변화 없음 | `diffs/upstream-v2.11.3-to-v2.13.0.diff` |
| current canonical vs target source | platform-neutral local `SKILL.md`, local eval, target script 2개 차이 | `diffs/canonical-v2.11.3-to-v2.13.0-source.diff` |
| target source vs runtime preview | local `SKILL.md` adaptation과 local eval만 차이; target script는 preview에 verbatim 반영 | `diffs/source-to-runtime-preview.diff` |

`SKILL.md`는 upstream v2.11.3과 v2.13.0에서 SHA-256이
`04e3332c3f82b3dfc60962477b834db1b0d1e2150cc4c96d7139150df612ad1f`로 같다.
따라서 local adaptation을 보존하는 3-way merge는 conflict 없이 clean이다.

## reference-only 소비자 영향

| 소비자 | 현재 의미 계약 | 후보에서의 처리 |
|---|---|---|
| `design-prototype-docs` | 승인된 `ui-ux-pro-max` 결정을 입력으로 사용 | 파일 복사 없음 |
| `create-prototype` | 기존 디자인 시스템 다음의 입력으로 사용 | 파일 복사 없음 |
| `frontend-design` | 제품 토큰 다음의 승인된 입력으로 사용 | 파일 복사 없음 |
| `impl-verify` | 직접 upstream 의존 없음 | 파일 복사 없음 |

## license 상태

Git `core.autocrlf`를 끈 archive raw bytes 기준으로 upstream v2.11.3과 v2.13.0의
`LICENSE` SHA-256은 모두
`738f69dfa83db5c347c678fb9d90e560877059f0de93a327c39001bff92dc014`이며 MIT text는
변하지 않았다. 이 값은 기존 provenance 사본, registry 및 NOTICE의 accepted evidence와
일치한다.

## 결론

Phase 3 검토 결과 후보는 `accept-for-staging`이다. LICENSE는 MIT이며 raw archive
SHA-256, 저작권 표기와 전문이 baseline·기존 accepted provenance와 모두 같다. 변경된
script/test는 Python 표준 라이브러리와 local module만 import하고, network, subprocess,
shell, dynamic execution을 사용하지 않는다. runtime preview test는 36 passed다.

Codex와 Claude Code는 plugin runtime의 물리 경로와 호출 표면만 다르다
(`runtime/codex/skills/**`의 `$ui-ux-pro-max`, `runtime/claude/skills/**`의
`/harness-kit:ui-ux-pro-max`). 빌더는 같은 canonical skill payload를 두 runtime으로
복사하므로 이번 candidate에는 host별 의존성이나 동작 차이가 없다. 실제 CLI·앱 모델 호출
증적은 release gate에서 별도로 남긴다.

보호 자산은 수정 script 1개와 추가 test 1개이므로 G4 명시 승인 없이는 promotion하지
않는다. 삭제·이동은 없어서 G5는 불필요하며, G3 일반 적용 승인은 promotion handoff 전에만
받는다.
