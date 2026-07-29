<!-- 산출물 예시 메타 -->
> 📂 **산출물 예시 — `harness-setup` bridge (CLAUDE.md)**
> 산출 경로: 프로젝트 루트 `CLAUDE.md`
> 현행 기준에서 `CLAUDE.md`는 프로젝트 컨텍스트 정본이 아닙니다. Claude가 공용 정본인 `AGENTS.md`를 읽도록 연결하는 bridge 예시입니다.

---

# Claude Code Bridge

이 프로젝트의 공용 에이전트 컨텍스트 정본은 `AGENTS.md`입니다.

@AGENTS.md

Claude Code는 위 파일을 먼저 읽고, `.docs/`의 세부 instruction과 설계·구현 문서를 참조합니다.

주의:

- `CLAUDE.md`에 `AGENTS.md`와 같은 본문을 중복 작성하지 않는다.
- 프로젝트 규칙 변경은 `AGENTS.md`와 `.docs/` 원본에 반영한다.
- 복수 앱 프로젝트에서는 `.docs/root-context/AGENTS.md`를 관리 원본으로 두고 루트 `AGENTS.md`/`CLAUDE.md`는 실행용으로 갱신한다.
