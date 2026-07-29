# Plugin Installation Guide

> 기준일: 2026-07-29
> 대상 플러그인: `ai-agent-harness` `0.1.0`
> 현재 상태: 공식 manifest·marketplace와 격리 CLI smoke를 자동 검증한다. Codex와 Claude 앱의 설치·재시작·새 세션 증적까지 확보되기 전에는 `not release-ready`다.

이 문서는 실제 프로젝트 사용자가 하네스 저장소를 clone하거나 스킬을 복사하지 않고 플러그인으로 시작하기 위한 설치·확인·업데이트·제거 기준이다.

---

## 1. 먼저 알아야 할 것

- 이 저장소는 관리자용 원본 저장소다.
- 실제 프로젝트에는 `plugins/ai-agent-harness` 또는 배포된 marketplace source를 통해 플러그인을 설치한다.
- 설치 후 새 task/session 또는 reload가 필요하다.
- 프로젝트에서는 `harness-setup`을 호출해 `.docs/**`, 루트 `AGENTS.md`, `CLAUDE.md`만 만든다.
- `harness-setup`은 사용자 프로젝트에 `.agents/skills/`, `.claude/skills/`, `skills/`를 생성하거나 스킬을 복사·동기화하지 않는다.
- `.md` 산출물 후처리는 별도 `im-not-ai` 설치 없이 내장 `humanize-korean`을 쓴다.

---

## 2. 현재 릴리스 후보 정보

| 항목 | 값 |
|------|----|
| Plugin ID | `ai-agent-harness` |
| Version | `0.1.0` |
| Local plugin root | `plugins/ai-agent-harness` |
| Archive | `plugins/ai-agent-harness-0.1.0.zip` |
| Archive SHA-256 | `maintainer/plugin/release.json`의 현재 생성값 |
| Codex physical skills | 18 |
| Codex agents | 0 |
| Claude physical skills | 18 |
| Claude agents | 0 |
| Release gate | `not-release-ready` |

릴리스 게이트 증적은 [maintainer/plugin/release-checklist.md](../maintainer/plugin/release-checklist.md)와 [maintainer/plugin/install-verification.json](../maintainer/plugin/install-verification.json)에 있다.

---

## 3. Codex CLI

공식 Codex CLI `0.146.0`을 임시 `CODEX_HOME`에서 실행해 아래 marketplace
등록·설치·목록·제거 흐름과 설치 cache의 18 skills / 0 agents를 확인했다. CI도
같은 격리 smoke를 반복하고, 배포 전 실제 사용자 CLI에서 한 번 더 확인한다.

### 3-1. marketplace source 관리

Git-backed marketplace를 사용하는 경우:

```text
codex plugin marketplace add <github-owner/repo | git-url | 저장소-루트-경로>
codex plugin marketplace list
```

`marketplace add`에는 source 하나만 전달한다. Git ref를 고정하려면 `--ref`를
사용한다. 저장소 루트의 `.agents/plugins/marketplace.json`이
`ai-agent-harness` marketplace를 노출한다.

업데이트는 marketplace를 갱신한 뒤 plugin을 재설치하는 방식으로 검증한다.

```text
codex plugin marketplace upgrade ai-agent-harness
codex plugin remove ai-agent-harness@ai-agent-harness
codex plugin add ai-agent-harness@ai-agent-harness
```

### 3-2. 비대화식 설치 관리

```text
codex plugin add ai-agent-harness@ai-agent-harness
codex plugin list
codex plugin remove ai-agent-harness@ai-agent-harness
```

설치 후 새 task를 열고 `harness-setup`, `humanize-korean`이 감지되는지 확인한다.

### 3-3. 대화형 설치

Codex 대화형 표면에서는 `/plugins` UI로 설치·활성화·비활성화를 확인한다. CLI 설치와 UI 설치는 캐시·활성 session이 다를 수 있으므로 둘을 별도 증적으로 남긴다.

### 3-4. Codex IDE extension

Phase 8 기준 Codex IDE extension은 별도 공식 플러그인 설치 표면으로 보지 않는다. 프로젝트에서 확장이 Codex CLI/App 플러그인 상태를 공유하지 않으면 `AGENTS.md`와 `.docs` 산출물만 일반 프로젝트 문서로 참조한다.

---

## 4. ChatGPT/Codex Desktop/App

Desktop/App에서는 다음을 수동으로 확인한다.

1. Plugins Directory를 연다.
2. Git-backed marketplace repository 또는 local marketplace root를 추가한다.
3. `ai-agent-harness` `0.1.0`을 설치한다.
4. 앱을 재시작하거나 새 task/session을 연다.
5. `harness-setup`과 `humanize-korean`이 보이는지 확인한다.
6. 새 버전 후보를 설치하거나 stale cache를 비운 뒤 version marker가 갱신되는지 확인한다.

자동 검증은 package와 CLI까지만 수행하며 Desktop/App 결과는 `manual-required`다.

---

## 5. Claude Code CLI

공식 Claude Code `2.1.220`을 별도 `CLAUDE_CONFIG_DIR`과 plugin cache에서 실행해
아래 흐름과 설치 cache의 18 skills / 0 agents를 확인했다. CI도 같은 격리 smoke를
반복한다.

```text
claude plugin validate plugins/ai-agent-harness --strict
claude plugin validate . --strict
claude plugin marketplace add <github-owner/repo | git-url | 저장소-루트-경로>
claude plugin marketplace list
claude plugin install ai-agent-harness@ai-agent-harness
claude plugin list
/reload-plugins
```

업데이트와 제거:

```text
claude plugin marketplace update ai-agent-harness
claude plugin update ai-agent-harness@ai-agent-harness
claude plugin uninstall ai-agent-harness@ai-agent-harness
```

검증:

- `harness-setup` 호출 가능
- namespaced `ai-agent-harness:humanize-korean` 호출 가능
- `.claude-plugin/plugin.json`의 version 확인
- `/reload-plugins` 후 새 skill 목록 확인

---

## 6. Claude Desktop Code 탭

Claude Desktop Code 탭과 CLI는 설정을 공유하지만 host별 plugin cache와 활성 세션을
따로 확인해야 한다.

1. local host 설치
2. SSH host 설치
3. 앱 재시작
4. 새 Code session
5. `harness-setup`, `humanize-korean` 노출 확인
6. cloud Code 세션은 plugin browser가 없어 프로젝트 `enabledPlugins` 정책을 별도 적용
7. WSL session은 Desktop plugin 설치 표면으로 지원하지 않음을 명시

Phase 7 자동 검증 결과: `manual-required`.

---

## 7. Claude Chat/Cowork

Claude Chat/Cowork는 Claude Code 플러그인과 같은 설치 표면으로 취급하지 않는다.

- Code 탭에서 검증된 플러그인이 Chat/Cowork에서 자동 활성화된다고 가정하지 않는다.
- Chat/Cowork에서 같은 스킬을 쓰려면 별도 프로젝트/워크스페이스 지침, 권한, 파일 접근 범위를 문서화한다.
- 사용자가 Code와 Chat을 오가면 최종 기준 문서는 프로젝트의 `AGENTS.md`와 `.docs`로 둔다.

---

## 8. private GitHub와 cache

Private GitHub source를 사용할 때 확인할 것:

- CLI/App이 GitHub 인증 정보를 읽을 수 있는지
- 조직 SSO나 PAT 권한이 marketplace/source clone에 충분한지
- stale cache가 남아 이전 버전을 로드하지 않는지
- 새 session에서 version marker가 바뀌는지
- 실패 시 원본 프로젝트 파일을 건드리지 않고 plugin cache만 재설치하는지

보수 재설치 절차:

```text
codex plugin list 또는 claude plugin list
플랫폼별 plugin remove/uninstall ai-agent-harness@ai-agent-harness
플랫폼별 plugin marketplace upgrade/update ai-agent-harness
플랫폼별 plugin add/install ai-agent-harness@ai-agent-harness
새 task/session
version marker 확인
```

---

## 9. 설치 후 첫 하네스 설정

플러그인을 설치한 뒤 프로젝트에서 다음 순서로 진행한다.

```text
harness-setup 실행
→ 단일/복수 앱 확인
→ .docs 생성 또는 갱신
→ AGENTS.md 생성 또는 갱신
→ CLAUDE.md bridge 생성 또는 갱신
→ .agents/skills·.claude/skills·skills 미생성 확인
→ design-doc/context-doc/harness-bootstrap로 프로젝트 문서화
```

복수 앱에서는 `.docs/root-context/AGENTS.md`가 루트 컨텍스트의 관리 원본이다. 루트 `CLAUDE.md`는 `AGENTS.md`를 읽도록 하는 bridge로 둔다.

---

## 10. Markdown 산출물 후처리

다음 스킬은 `.md` 산출물을 만들 수 있다.

- `harness-setup`
- `harness-bootstrap`
- `context-doc`
- `design-doc`
- `design-prototype-docs`
- `impl-doc`
- `impl-fe-be-doc`

산출물 생성 후 흐름:

```text
원 producer 검증
→ 최외곽 producer가 artifact_bundle_id와 handoff_owner 확정
→ 중첩 producer는 suppress_child_handoff=true로 별도 제안 억제
→ bundle을 humanize-korean document-refinement profile에 한 번만 전달
→ 개선안과 diff 확인
→ 보호 token·링크·표·코드블록 보존 확인
→ 사용자 승인
→ 승인된 파일만 반영
→ 원 producer의 구조·index·bridge 재검증
```

`humanize-korean`은 기본적으로 proposal-only다. 사용자가 승인하지 않으면 원본 파일을 변경하지 않는다.

---

## 11. 기존 local skill copy 마이그레이션

기존 프로젝트에 `.agents/skills` 또는 `.claude/skills`가 남아 있을 수 있다. 이 경우 기본 동작은 삭제가 아니라 읽기 전용 inventory다.

분류:

- known old harness copy
- user-modified old copy
- unknown custom skill

삭제 또는 이동은 다음 조건을 만족해야 한다.

1. 백업 대상 확인: `.docs/archive/legacy-agent-skills/{timestamp}/`
2. 사용자 승인
3. backup/remove 실행
4. 플러그인 단일 discovery 확인
5. 문제 발생 시 백업 복원

산출물, 스크립트, 템플릿을 가진 스킬은 자동 제거하지 않는다.

---

## 12. 문제 해결

| 증상 | 조치 |
|------|------|
| 스킬이 보이지 않음 | 새 task/session, `/reload-plugins`, 앱 재시작을 먼저 수행 |
| 구버전이 보임 | plugin version marker와 cache를 확인하고 remove/add |
| Codex CLI가 실행되지 않음 | CLI 자체 권한/설치 문제를 먼저 해결하고, 필요하면 공식 npm 패키지를 임시 `CODEX_HOME`에서 검증 |
| Claude CLI가 없음 | 공식 Claude Code CLI를 설치하거나 격리된 npm package 실행으로 명령 surface 재검증 |
| `humanize-korean`이 원본을 바꾸려 함 | 중단. proposal-only 계약 위반으로 보고 |
| local copy와 plugin skill이 중복됨 | inventory 후 승인형 backup/remove 절차 수행 |
| setup 후 새 skill 디렉터리가 생김 | 중단. `.docs/**`, `AGENTS.md`, `CLAUDE.md` 출력 allowlist 위반으로 보고 |
