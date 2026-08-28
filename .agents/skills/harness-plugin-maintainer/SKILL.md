---
name: harness-plugin-maintainer
description: "관리자가 사용자용 harness-kit 플러그인의 Codex·Claude runtime projection, manifest, smoke test, 릴리스 후보를 생성·검증할 때 사용한다. 사용자 스킬 upstream 품질 개선 자체는 담당하지 않는다."
allowed-tools: Read, Write, Glob, Grep
disable-model-invocation: true
---

# Harness Plugin Maintainer

사용자 플러그인 생성과 검증을 관리하는 관리자 전용 스킬이다.
생성된 plugin tree와 archive를 교체할 수 있으므로 명시 호출 전용이다. 이 관리
저장소에서 Codex는 `$harness-plugin-maintainer`, Claude Code는
`/harness-plugin-maintainer`로 호출하고 build·check·smoke 중 수행 범위를 적는다.

## 책임

- `skills/` 사용자 정본에서 Codex·Claude 사용자 플러그인 runtime을 생성한다.
- plugin manifest, 버전, checksum, smoke test를 검증한다.
- repo-local 관리자 projection을 생성해 관리자가 이 저장소에서만 관리자 스킬을 사용할 수 있게 한다.

## 비책임

- 외부 공식·유명 스킬의 내용 평가와 upstream 최신화 후보 선정
- 사용자 프로젝트에 `.docs` 또는 루트 컨텍스트를 직접 생성
- 관리자 스킬을 사용자 플러그인 payload에 포함

## 운영 원칙

- `maintainer/plugin/CAPABILITIES.json`의 논리 사용자 스킬만 payload에 포함한다. 스킬 수는 이 inventory에서 파생하며 문서나 스크립트에 숫자를 고정하지 않는다.
- `maintainer/skills/**`, `.agents/skills/**`, `.claude/skills/**` 관리자 projection은 payload에 포함하지 않는다.
- build는 결정적이어야 한다. 같은 source에서 두 번 생성한 파일 목록·내용·archive hash가 같아야 한다.
- 패키지에 들어가지 않는 정본 변경은 archive hash를 바꾸지 않아야 한다. `lifecycle`이 `candidate`인 관계와 source lock의 문서 수준 타임스탬프는 packaged lock에 반영하지 않는다.
- release manifest 두 개(`.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`)는 같은 plugin ID와 같은 semantic version을 사용한다.
- `im-not-ai` 등 runtime direct import는 plugin NOTICE와 `licenses/{upstream-id}-LICENSE`에 닫혀야 한다.
- `UPSTREAMS.lock.json`의 `packaged`는 artifact 검증 후에만 갱신한다. `released`는 이 스킬에서 갱신하지 않는다.
- push, tag, GitHub release 생성은 별도 명시 승인 전 수행하지 않는다.

## 버전 승격 기준

SemVer 규격의 자동 귀결이 아니라 이 저장소의 자체 정책이다. SemVer는 `0.y.z`를
초기 개발 단계로 규정하고 공개 API 안정성을 보장하지 않으므로, `0.x`에서
breaking 변경을 어느 자리로 올릴지는 규격이 정해주지 않는다.

| 변경 성격 | `0.x` | `1.0` 이후 |
|---|---|---|
| 스킬 이름·호출 계약·필수 입력·설치 인터페이스·산출물 경로의 제거·변경 | 다음 MINOR로 올리고 changelog에 breaking 명시 | MAJOR |
| 사용자 스킬 추가, 공개 capability 추가, 선택적 산출물 추가 | 다음 MINOR | MINOR |
| 공개 동작을 바꾸지 않는 버그·문서·증적 수정 | PATCH | PATCH |

`1.0.0`은 배포를 한 번 수행했다는 사실로 정하지 않는다. 공개 스킬 이름, 호출
계약, 필수 입력, 산출물 경로, 설치 인터페이스가 안정되어 이후 변경을 BREAKING으로
관리할 준비가 됐을 때 정한다.

이미 감사 산출물에 archive hash가 기록된 버전 번호로 내용이 다른 산출물을
재빌드하지 않는다.

## eval runner coverage

`scripts/run_all_skill_evals.py`는 runner를 glob으로 탐색하므로 runner가 없는
스킬은 조용히 검사에서 빠지고 로그는 전체 통과로 보인다.
`maintainer/inventory/skill-eval-coverage.json`이 정본이며 여기에 `required`로
선언된 runner가 없으면 실패시킨다. 모든 스킬에 runner를 강제하지는 않는다.

## 실행 절차

### 1. inventory

다음을 읽는다.

- `skills/**`
- `maintainer/plugin/CAPABILITIES.json`
- `maintainer/plugin/runtime-allowlist.json`
- `maintainer/inventory/markdown-artifact-flow.json`
- `maintainer/inventory/skill-eval-coverage.json`
- `maintainer/upstreams/lock.json`
- `maintainer/upstreams/registry.json`
- `maintainer/upstreams/provenance/**`

### 2. build

`scripts/build_plugin.py`를 실행한다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py
```

생성 대상:

```text
repo root/
  .agents/plugins/marketplace.json
  .claude-plugin/marketplace.json
plugins/harness-kit/
  .codex-plugin/plugin.json
  .claude-plugin/plugin.json
  runtime/codex/skills/**
  runtime/claude/skills/**
  LICENSE
  licenses/{upstream-id}-LICENSE
  THIRD_PARTY_NOTICES.md
  CAPABILITIES.json
  UPSTREAMS.lock.json
```

### 3. validate

`scripts/validate_plugin.py`를 실행한다.

검사:

- logical user skill 수는 `CAPABILITIES.json`에서 파생한다
- 관리자 스킬 0
- Codex·Claude physical skill 수는 inventory와 일치, agent 0
- `humanize-korean`만 canonical 문서 개선 스킬로 패키징
- manifest `name`과 marketplace `name`이 kebab-case 공식 식별자 형식
- Codex·Claude marketplace가 관리 저장소 루트에서 `./plugins/harness-kit`를 가리킴
- Markdown producer는 inventory에서 파생하며 각 producer가 public handoff를 선언
- `model:`과 `agent: fork` 금지
- plugin root 밖 상대경로 금지
- 모든 packaged adapted·vendored source의 NOTICE·license·lock closure
- archive mode와 LF line ending, generated metadata marker

### 4. check

`build_plugin.py --check`와 `validate_plugin.py`를 함께 실행한다. `--check`는 임시 디렉터리에 expected artifact를 생성해 canonical plugin tree, archive, release metadata, repo-root marketplace와 비교하며 canonical 파일을 수정하지 않는다. drift가 있으면 source나 builder를 고친 뒤 다시 build한다.

### 5. handoff

검증된 release candidate 정보를 `maintainer/plugin/release.json`에 기록한다. release-ready 판단과 실제 설치 검증은 Phase 7에서 수행한다.

### 6. 설치 인터페이스 검증

`scripts/smoke_cli_install.py`로 Codex와 Claude Code의 실제 CLI 설치 흐름을 격리
검증하고, `scripts/verify_install_surfaces.py`로 릴리스 게이트 증적을 갱신한다.

- CLI smoke는 임시 `CODEX_HOME`, `CLAUDE_CONFIG_DIR`,
  `CLAUDE_CODE_PLUGIN_CACHE_DIR`만 사용한다.
- CI·eval에서는 `verify_install_surfaces.py --check`로 실행한다. host별
  `cli_probes` 차이는 제외하되 plugin version·archive hash·skill 수·migration
  fixture·release checklist 같은 결정적 증적은 계속 비교한다. 증적 갱신은
  관리자가 기본 모드로 명시 실행할 때만 수행한다.
- 양쪽 모두 marketplace 등록 → plugin 설치 → 목록과 설치 cache의 inventory 기준 skill 수 /
  0 agents 확인 → uninstall/remove까지 수행한다.
- desktop/app/SSH 등 대화형 인터페이스는 release checklist에 수동 검증 항목으로 남긴다.
- local에서 가능한 release candidate metadata, archive checksum, `humanize-korean` proposal-only, legacy local skill copy migration fixture를 검증한다.
- 네 가지 핵심 인터페이스(Codex CLI·Codex 앱·Claude Code CLI·Claude 앱) 증적이 모두 없으면 `release-ready`로 표시하지 않는다.

### 7. release regression

Phase 10에서는 `scripts/run_release_regression.py`를 실행한다.

- clean build를 두 번 수행해 archive hash와 manifest가 같은지 확인한다.
- source, manager projection, plugin projection의 수·역할·alias mapping을 확인한다.
- 문서 로컬 링크, upstream registry/provenance, plugin NOTICE/license closure를 회귀 검증한다.
- reference, vendored, adapted 세 upstream 관리 모드는 임시 mirror에서만 end-to-end로 시뮬레이션한다.
- 사용자 end-to-end는 임시 프로젝트에서 `harness-setup` 결과 구조, `humanize-korean` proposal-only, 승인 후 재검증 흐름을 검증한다.
- 실패 주입과 rollback은 임시 released lock/plugin version fixture에서만 수행한다.
- push, tag, GitHub release, `released` lock 갱신은 별도 승인 전 수행하지 않는다.

관리자 스킬 freeze는 UTF-8 텍스트의 줄바꿈을 LF로 정규화해 hash하고,
대소문자 영향을 받지 않는 POSIX 상대경로 순서로 고정한다.
CI·eval은 `freeze_manager_inventory.py --check`로 비교만 하며 정본을 쓰지 않는다.

## 검증

```bash
python maintainer/skills/harness-plugin-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/run_all_skill_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/smoke_cli_install.py --output maintainer/plugin/cli-smoke.json
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/freeze_manager_inventory.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/run_release_regression.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
```
