@AGENTS.md

## Claude Code 전용 차이

- 공통 운영 규칙은 `AGENTS.md`를 따른다.
- 이 저장소의 Claude용 repo-local 스킬은 `.claude/skills/` projection에서 발견된다.
- `.claude/skills/`는 생성물이다. 수정은 `maintainer/skills/` 정본에서 수행한 뒤 projection 생성기로 반영한다.
- 사용자 프로젝트의 산출물 위치는 해당 프로젝트의
  `@.docs/instruction/artifact-output-routing-instruction.md`(복수 앱은
  `@.docs/{앱}/instruction/artifact-output-routing-instruction.md`)를 따른다.
