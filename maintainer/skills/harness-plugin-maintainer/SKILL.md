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

## Phase 1 상태

이 파일은 Phase 1의 골격이다. plugin packaging 상세 구현은 Phase 6에서 수행한다.
