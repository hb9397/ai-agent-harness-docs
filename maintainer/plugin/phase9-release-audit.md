# 최종 감사 — `0.2.2` 릴리스 후보

생성 시각: 2026-08-01

> Historical report: 이 문서는 `0.2.2` 후보의 감사 기록이다. 현재 `harness-kit`
> `0.4.0` 후보의 live metadata와 설치 증적은 `release.json`,
> `release-checklist.md`, `install-verification.json`을 따른다.

대상 계획서: `improvement_plan/20260730/UI UX Pro Max 및 Motion Design 업스트림 통합 작업 계획서.md`

## 판정

**`not-release-ready`**

자동 검증과 CLI 설치 smoke는 모두 통과했다. 네 실행 표면의 **실제 모델 호출
수동 증적**이 아직 없으므로 릴리스 준비 완료로 표시하지 않는다.

## 릴리스 후보

| 항목 | 값 |
|---|---|
| 플러그인 ID | `ai-agent-harness` |
| 버전 | `0.2.2` |
| 아카이브 | `plugins/ai-agent-harness-0.2.2.zip` |
| 아카이브 SHA-256 | `016be105eaebf46f164641946c1705edbf1b70bed7a3bf4aff661a6e0814d27c` |
| 논리 사용자 스킬 | 20 |
| 관리자 스킬 | 3 (payload 제외) |
| Codex 물리 스킬 / agent | 20 / 0 |
| Claude 물리 스킬 / agent | 20 / 0 |
| Markdown producer | 9 (고정 7 + 조건부 2) |
| 본체 라이선스 | Apache-2.0, `hb9397` |

`release.json`, `install-verification.json`, `release-checklist.md`가 모두 같은
archive 해시를 기록한다.

### 버전 이력

| 버전 | 성격 | 사유 |
|---|---|---|
| `0.1.0` | 기준선 | 이번 작업 이전 상태. 감사 증적은 역사 기록으로 보존한다. |
| `0.1.1` | PATCH | `pre-commit` eval의 오탐 수정. 공개 동작 변경 없음. |
| `0.2.0` | MINOR | 사용자 스킬 2종 추가, 기존 4종의 선택적 산출물과 검증 항목 확대. |
| `0.2.1` | PATCH | 저장소 개명(`AI_Agent_docs` → `ai-agent-harness-docs`)에 따른 manifest·marketplace·NOTICE URL 정정. 공개 동작 변경 없음. |
| `0.2.2` | PATCH | 관리 저장소 운영문서를 `.user-docs/`로 이전하고, 공개 사용자 계약 변경 없이 정본·검증·runtime 참조를 정합화. 교육자료 제거. |

## Packaged upstream

| source | ref | commit |
|---|---|---|
| `anthropic-frontend-design` | `main` | `b29e7cf65e5cb78a5ac33d582270551bc74a14eb` |
| `im-not-ai` | `v2.3.0` | `82137e858763dadb99561f194c5c00465735017b` |
| `ui-ux-pro-max-runtime` | `v2.11.3` | `4857a2c5ef989794751a0f66b8545a4a49566286` |
| `lottiefiles-motion-design-runtime` | `main` | `f9a8a041b85185ee4881b3471d3415e939aac772` |

참고 관계 `ui-ux-pro-max-principles`와 `lottiefiles-motion-design-principles`는
파일을 복사하지 않으므로 `licenses/` 패키징 대상이 아니다. 각 관계 그룹은 같은
commit을 가리킨다.

## 자동 증적 (TEST-014)

| 검증 | 결과 |
|---|---|
| `skill-portfolio-maintainer/evals/run_evals.py` | PASS |
| `harness-plugin-maintainer/evals/run_evals.py` | PASS |
| `run_all_skill_evals.py` (14 runners + 통합 fixture 2종) | PASS |
| `build_plugin.py --check` | PASS |
| `validate_plugin.py` | PASS |
| `verify_install_surfaces.py --check` | PASS |
| `freeze_manager_inventory.py --check` | PASS |
| `run_release_regression.py` | PASS |
| `sync_manager_projections.py --check` | PASS |
| `validate_registry.py` | PASS |
| `git diff --check` | PASS |

2회 연속 실행에서 모두 통과했다. 같은 source로 두 번 build한 archive 해시가
동일하다.

### 검증 안정성에 대한 기록

TEST-014 초기 실행에서 간헐적 실패가 있었다. 원인은 Windows에서 파일을 제자리에
다시 여는 쓰기 패턴이 스캐너 핸들과 충돌해 `OSError(EINVAL)`을 내는 것이었다.
다음을 적용해 해소했다.

- JSON·텍스트 쓰기를 임시 파일 + `os.replace`로 원자화
- archive 쓰기도 같은 방식으로 원자화
- `rmtree`, `rename`, `copytree`에 제한적 재시도 적용
- 빌드를 staging 디렉터리에 조립한 뒤 교체해, 실패해도 기존 트리가 남게 함

적용 후 2회 연속 전체 통과했다. 이 항목은 산출물 내용이 아니라 검증 실행
환경의 문제였으며, 아티팩트 해시는 변하지 않았다.

## 의도 재감사 (TEST-015)

| # | 질문 | 판정 |
|---|---|---|
| 1 | 두 신규 스킬은 독립 호출 가능한가 | PASS |
| 2 | 원본의 실행·참조 자산을 모두 패키징하는가 | PASS |
| 3 | direct/reference 관계가 같은 SHA를 가리키는가 | PASS |
| 4 | 기존 스킬이 외부 내부 경로에 결합되지 않았는가 | PASS |
| 5 | 디자인 흐름이 일반 흐름을 복잡하게 만들지 않는가 | PASS |
| 6 | 프로토타입과 제품 source 경계가 지켜지는가 | PASS |
| 7 | 모션을 필요 없는 화면에 강제하지 않는가 | PASS |
| 8 | 사용자 프로젝트에 local skill 디렉터리를 만들지 않는가 | PASS |
| 9 | Caveman·Ruflo가 별도 설치 대상으로만 설명되는가 | PASS |
| 10 | 문서·manifest·runtime의 skill count가 모두 20인가 | PASS |
| 11 | 본체·플러그인 라이선스에 플레이스홀더가 없는가 | PASS |
| 12 | 생성물의 저작권 귀속이 실제 저장소를 가리키는가 | PASS |
| 13 | 스킬 수·producer 수가 inventory에서 파생되는가 | 최초 오판 후 수정 |
| 14 | runner 없는 스킬이 보고되는가 | PASS |

### 13번 오판 정정

최초 감사에서 13번을 PASS로 기록했으나 이는 잘못이었다. 감사 스크립트가
`!= 18`, `== 18` 같은 비교 연산자만 검사하고 **문자열 리터럴을 놓쳤다.**
외부 검토에서 다음이 드러났다.

- `verify_install_surfaces.py`가 릴리스 체크리스트 본문에 "스킬 18개"를
  하드코딩해, 실제 20종인데도 18종이라 주장하는 체크리스트를 생성하고
  `--check`는 자기 자신과 비교하므로 통과했다.
- `.user-docs/Plugin_Installation_Guide.md`, `.user-docs/Harness_Engineering.md`,
  `harness-plugin-maintainer/SKILL.md`, `references/plugin-structure.md`에
  18종·7종 표현이 남아 있었다.

체크리스트 생성기는 실제 설치 증적의 `skill_count`에서 값을 읽도록 바꿨고,
문서 4곳은 20종·9종 또는 inventory 파생 표현으로 정정했다.
`final-readiness-audit.*`의 18은 `0.1.0` 역사 기록이므로 유지한다.

## 표면별 증적

| 표면 | 상태 | 증적 |
|---|---|---|
| Codex CLI | `install-smoke-verified` | Codex CLI `0.146.0`, payload `0.2.2` / 20 skills / 0 agents / cleanup passed. **모델 호출 미검증.** |
| Codex Desktop/App | `manual-required` | 대화형 Plugins UI 표면이 필요하다. |
| Claude Code CLI | `install-smoke-verified` | Claude Code `2.1.220`, payload `0.2.2` / 20 skills / 0 agents / cleanup passed. **모델 호출 미검증.** |
| Claude Desktop Code | `manual-required` | Desktop Code 앱 표면이 필요하다. |

판정 규칙에 따라 자동 설치 성공을 모델 동작 성공으로 대신하지 않고, CLI 성공을
앱 성공으로 대신하지 않는다.

## 릴리스 전 남은 작업

1. 네 표면에서 `maintainer/plugin/manual-surface-test-template.md`의 시나리오
   A~H를 수행한다. E~H는 이번에 추가한 디자인 흐름 검증이다.
2. 완료본을 `maintainer/plugin/manual-evidence/YYYYMMDD/{surface}.md`에 저장하고
   릴리스 체크리스트에 연결한다.
3. 네 표면의 검토자 확인이 끝난 뒤에만 상태를 `verified`로 바꾼다.
4. 미지원 표면은 `SKIP`이 아니라 근거가 있는 `미지원`으로 기록한다.

## 릴리스 통제

- 릴리스 준비 완료: 아니요
- push 생성: 아니요
- tag 생성: 아니요
- GitHub release 생성: 아니요
- `released` lock 갱신: 아니요
- 배포 전 명시적인 관리자 승인 필요: 예
