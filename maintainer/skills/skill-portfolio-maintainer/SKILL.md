---
name: skill-portfolio-maintainer
description: "관리자가 사용자 스킬 포트폴리오의 외부 공식·유명 스킬 참고 관계, provenance, protected asset 영향, upstream 최신화 후보를 조사하고 반영 계획을 관리할 때 사용한다. 사용자 플러그인 패키징이나 릴리스 생성은 담당하지 않는다."
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Skill Portfolio Maintainer

사용자 스킬셋의 품질과 provenance를 관리하는 관리자 전용 스킬이다.

## 책임

- `skills/` 사용자 스킬의 upstream 관계를 `native`, `reference`, `adapted`, `vendored`로 분류한다.
- 공식 스킬, 외부 유명 스킬, GitHub release를 조사해 반영 후보를 만든다.
- protected asset, templates, scripts, examples 변경 영향을 분리한다.
- 삭제·이동·교체가 필요한 경우 별도 파괴적 변경 승인 항목으로 분리한다.

## 비책임

- Codex·Claude 플러그인 manifest 생성
- 사용자 플러그인 release archive 생성
- `.agents/skills` 또는 `.claude/skills` projection 생성

## Phase 1 상태

이 파일은 Phase 1의 골격이다. 상세 절차, scripts, evals는 Phase 5에서 구현한다.
