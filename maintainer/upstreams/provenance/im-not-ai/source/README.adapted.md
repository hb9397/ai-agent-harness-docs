# im-not-ai adapted 소스 스냅샷

이 디렉터리는 로컬 `humanize-korean` 스킬에 대해 승인된, 저장해도 안전한
소스 기준을 기록한다.

업스트림 저장소 전체를 vendored 방식으로 반입하지 않는다. Phase 4에서는 다음
항목만 승격한다.

- 로컬에서 다시 작성한 `skills/humanize-korean/SKILL.md`
- `skills/humanize-korean/references/` 아래의 축약된 로컬 참고 자료
- `skills/humanize-korean/scripts/` 아래의 결정적 로컬 보호 스크립트
- `maintainer/upstreams/provenance/im-not-ai/` 아래의
  `notice`/`license`/`provenance` 메타데이터

승인된 업스트림:

- 저장소: https://github.com/epoko77-ai/im-not-ai
- 태그: v2.3.0
- 커밋: 82137e858763dadb99561f194c5c00465735017b

의미 기반 변환 참고 사항:

- 업스트림 v2.3.0은 근거에 기반한 구간(span) 단위 편집을 요구하며, 매핑된
  발견 사항이 없는 텍스트는 변경하지 않는다.
- 로컬 결정적 보조 도구는 `~를 통해`, `~에 의해`, `결론적으로`의 담화 역할을
  판단할 수 없다.
- 따라서 이러한 표현은 가능한 수정안과 함께 문맥 검토 진단으로 보고하며,
  무조건적인 문자열 치환 대상으로 취급하지 않는다.
- 진단된 구간을 보존·삭제·수정할지는 보조 스크립트가 아니라 에이전트가 해당
  문장과 문단의 문맥을 확인한 뒤 결정한다.
