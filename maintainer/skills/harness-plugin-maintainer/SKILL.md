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
plugins/ai-agent-harness/
  .codex-plugin/plugin.json
  .claude-plugin/plugin.json
  .agents/plugins/marketplace.json
  .claude-plugin/marketplace.json
  runtime/codex/skills/**
  runtime/claude/skills/**
  runtime/claude/agents/**
  runtime/claude/im-not-ai-root/**
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
- Claude physical skill 20, agent 3
- `humanize`·`humanize-redo` alias가 `humanize-korean`으로 매핑
- Markdown producer 7종과 public handoff
- `model:`과 `agent: fork` 금지
- plugin root 밖 상대경로 금지
- NOTICE·license·lock closure
- generated marker 존재

### 4. check

`build_plugin.py --check`와 `validate_plugin.py`를 함께 실행한다. drift가 있으면 source나 builder를 고친 뒤 다시 build한다.

### 5. handoff

검증된 release candidate 정보를 `maintainer/plugin/release.json`에 기록한다. release-ready 판단과 실제 설치 검증은 Phase 7에서 수행한다.

### 6. install surface verification

Phase 7에서는 `scripts/verify_install_surfaces.py`를 실행한다.

- 현재 host의 Codex CLI와 Claude CLI 명령 표면을 probe한다.
- desktop/app/SSH 등 interactive surface는 release checklist에 수동 검증 항목으로 남긴다.
- local에서 가능한 release candidate metadata, archive checksum, `humanize-korean` proposal-only, legacy local skill copy migration fixture를 검증한다.
- 네 가지 핵심 surface(Codex CLI·Codex App·Claude Code CLI·Claude Desktop Code) 증적이 모두 없으면 `release-ready`로 표시하지 않는다.

## 검증

```bash
python maintainer/skills/harness-plugin-maintainer/evals/run_evals.py
python maintainer/skills/harness-plugin-maintainer/scripts/build_plugin.py --check
python maintainer/skills/harness-plugin-maintainer/scripts/validate_plugin.py
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
```
