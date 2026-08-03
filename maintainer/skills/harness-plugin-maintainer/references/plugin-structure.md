# harness-kit 플러그인 구조

생성된 플러그인은 단일 루트에 두 개의 매니페스트를 갖는 번들이다. Codex와
Claude는 로컬 플러그인 소스를 마켓플레이스 루트 기준 상대경로로 해석하므로,
마켓플레이스 카탈로그는 관리 저장소 루트에 둔다.

## 저장소 마켓플레이스 카탈로그

- Codex: `.agents/plugins/marketplace.json`
- Claude: `.claude-plugin/marketplace.json`
- 로컬 소스: `./plugins/harness-kit`

## 루트

`plugins/harness-kit/`

## Codex 런타임

- 매니페스트: `.codex-plugin/plugin.json`
- 스킬: `runtime/codex/skills`
- 물리적 스킬 수: 18
- `agents`: 없음

## Claude 런타임

- 매니페스트: `.claude-plugin/plugin.json`
- 스킬: `runtime/claude/skills`
- 물리적 스킬 수: 18
- 정본 문서 개선 스킬: `humanize-korean`
- `agents`: 없음

## 직접 반입 폐쇄 조건

모든 런타임 직접 반입은 다음 항목으로 폐쇄되어야 한다.

- `licenses/{upstream-id}-LICENSE`
- `THIRD_PARTY_NOTICES.md`
- `UPSTREAMS.lock.json`
- 소스 레지스트리 `file-map`

## 생성 메타데이터

공식 플러그인 매니페스트와 마켓플레이스 카탈로그에는 인식되는 스키마 필드만
포함한다. `CAPABILITIES.json`, `UPSTREAMS.lock.json`,
`MANIFEST.sha256.json`, `release.json` 같은 하네스 소유 메타데이터에는
`generated_by` 표식을 둔다. 런타임 스킬 파일은 소스에서 복사하며, 빌드 시
정규화는 줄바꿈만 변경하고 나머지 텍스트는 보존한다.

## 격리된 CLI 설치 스모크 테스트

결정적 빌드와 로컬 검증기를 통과한 뒤에만
`scripts/smoke_cli_install.py`를 실행한다. 이 스크립트는 임시 플랫폼 설정
디렉터리를 사용하며 Codex와 Claude Code 모두에서 다음을 검증해야 한다.

1. 저장소 루트 마켓플레이스 등록
2. `harness-kit@hb9397` 설치
3. 활성화된 플러그인 목록 표시
4. `CAPABILITIES.json`의 논리 스킬 수와 `agents` 0개를 기준으로 설치된 런타임의 일치 여부
5. `harness-setup`과 `humanize-korean`의 존재
6. 중첩된 마켓플레이스 카탈로그의 부재
7. 제거 및 마켓플레이스 정리

헤드리스 CLI 스모크 테스트로는 UI 검색, 재시작 동작, 새로 연 작업을 입증할 수
없으므로 Desktop/App 설치는 수동 릴리스 게이트로 유지한다.
