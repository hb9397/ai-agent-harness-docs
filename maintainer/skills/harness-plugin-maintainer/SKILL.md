---
name: harness-plugin-maintainer
description: "관리자가 사용자용 ai-agent-harness 플러그인의 Codex·Claude runtime projection, manifest, smoke test, 릴리스 후보를 생성·검증할 때 사용한다. 사용자 스킬 upstream 품질 개선 자체는 담당하지 않는다."
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Harness Plugin Maintainer

사용자 플러그인 생성과 검증을 관리하는 관리자 전용 스킬이다.

## 책임

- `skills/` 사용자 정본에서 Codex·Claude 사용자 플러그인 runtime을 생성한다.
- plugin manifest, 버전, checksum, smoke test를 검증한다.
- repo-local 관리자 projection을 생성해 관리자가 이 저장소에서만 관리자 스킬을 사용할 수 있게 한다.

## 비책임

- 외부 공식·유명 스킬의 내용 평가와 upstream 최신화 후보 선정
- 사용자 프로젝트에 `.docs` 또는 루트 컨텍스트를 직접 생성
- 관리자 스킬을 사용자 플러그인 payload에 포함

## 운영 원칙

- `skills/` 사용자 정본 18종만 payload에 포함한다.
- `maintainer/skills/**`, `.agents/skills/**`, `.claude/skills/**` 관리자 projection은 payload에 포함하지 않는다.
- build는 결정적이어야 한다. 같은 source에서 두 번 생성한 파일 목록·내용·archive hash가 같아야 한다.
- release manifest 두 개(`.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`)는 같은 plugin ID와 같은 semantic version을 사용한다.
- `im-not-ai` 등 runtime direct import는 plugin NOTICE와 `licenses/{upstream-id}-LICENSE`에 닫혀야 한다.
- `UPSTREAMS.lock.json`의 `packaged`는 artifact 검증 후에만 갱신한다. `released`는 이 스킬에서 갱신하지 않는다.
- push, tag, GitHub release 생성은 별도 명시 승인 전 수행하지 않는다.

## 실행 절차

### 1. inventory

다음을 읽는다.

- `skills/**`
- `maintainer/plugin/CAPABILITIES.json`
- `maintainer/plugin/runtime-allowlist.json`
- `maintainer/inventory/markdown-artifact-flow.json`
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
plugins/ai-agent-harness/
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

- logical user skill 18
- 관리자 스킬 0
- Codex physical skill 18, agent 0
- Claude physical skill 18, agent 0
- `humanize-korean`만 canonical 문서 개선 스킬로 패키징
- manifest `name`과 marketplace `name`이 kebab-case 공식 식별자 형식
- Codex·Claude marketplace가 관리 저장소 루트에서 `./plugins/ai-agent-harness`를 가리킴
- Markdown producer 7종과 public handoff
- `model:`과 `agent: fork` 금지
- plugin root 밖 상대경로 금지
- 모든 packaged adapted·vendored source의 NOTICE·license·lock closure
- archive mode와 LF line ending, generated metadata marker

### 4. check

`build_plugin.py --check`와 `validate_plugin.py`를 함께 실행한다. `--check`는 임시 디렉터리에 expected artifact를 생성해 canonical plugin tree, archive, release metadata, repo-root marketplace와 비교하며 canonical 파일을 수정하지 않는다. drift가 있으면 source나 builder를 고친 뒤 다시 build한다.

### 5. handoff

검증된 release candidate 정보를 `maintainer/plugin/release.json`에 기록한다. release-ready 판단과 실제 설치 검증은 Phase 7에서 수행한다.

### 6. install surface verification

`scripts/smoke_cli_install.py`로 Codex와 Claude Code의 실제 CLI 설치 흐름을 격리
검증하고, `scripts/verify_install_surfaces.py`로 릴리스 게이트 증적을 갱신한다.

- CLI smoke는 임시 `CODEX_HOME`, `CLAUDE_CONFIG_DIR`,
  `CLAUDE_CODE_PLUGIN_CACHE_DIR`만 사용한다.
- 양쪽 모두 marketplace 등록 → plugin 설치 → 목록과 설치 cache의 18 skills /
  0 agents 확인 → uninstall/remove까지 수행한다.
- desktop/app/SSH 등 interactive surface는 release checklist에 수동 검증 항목으로 남긴다.
- local에서 가능한 release candidate metadata, archive checksum, `humanize-korean` proposal-only, legacy local skill copy migration fixture를 검증한다.
- 네 가지 핵심 surface(Codex CLI·Codex App·Claude Code CLI·Claude Desktop Code) 증적이 모두 없으면 `release-ready`로 표시하지 않는다.

### 7. release regression

Phase 10에서는 `scripts/run_release_regression.py`를 실행한다.

- clean build를 두 번 수행해 archive hash와 manifest가 같은지 확인한다.
- source, manager projection, plugin projection의 수·역할·alias mapping을 확인한다.
- 문서 로컬 링크, upstream registry/provenance, plugin NOTICE/license closure를 회귀 검증한다.
- reference, vendored, adapted 세 upstream 관리 모드는 임시 mirror에서만 end-to-end로 시뮬레이션한다.
- 사용자 end-to-end는 임시 프로젝트에서 `harness-setup` 결과 구조, `humanize-korean` proposal-only, 승인 후 재검증 흐름을 검증한다.
- 실패 주입과 rollback은 임시 released lock/plugin version fixture에서만 수행한다.
- push, tag, GitHub release, `released` lock 갱신은 별도 승인 전 수행하지 않는다.

## 검증

```bash
python maintainer/skills/harness-plugin-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/smoke_cli_install.py
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py
python maintainer/skills/harness-plugin-maintainer/scripts/run_release_regression.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
```
