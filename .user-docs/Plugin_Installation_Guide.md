# Plugin Installation Guide

> 기준일: 2026-08-28
> 대상 플러그인: `harness-kit` `0.6.0`
> 현재 상태: `0.6.0`은 annotated tag와 [stable GitHub Release](https://github.com/hb9397/harness-kit/releases/tag/v0.6.0)로 게시됐다. 공식 manifest·marketplace 생성과 Codex·Claude CLI 격리 설치 smoke도 마쳤다.
> 다만 Codex와 Claude의 CLI·앱 네 인터페이스에서 실제 모델 호출·산출물·새 세션 증적은 아직 확보하지 못한 검증 한계로 남아 있다.

이 문서는 실제 프로젝트 사용자가 하네스 저장소를 clone하거나 스킬을 복사하지 않고 플러그인으로 시작하기 위한 설치·확인·업데이트·제거 기준이다.

---

## 1. 먼저 알아야 할 것

- 이 저장소는 관리자용 원본 저장소다.
- 실제 프로젝트에는 `plugins/harness-kit` 또는 배포된 marketplace source를 통해 플러그인을 설치한다.
- 설치 후 새 task/session 또는 reload가 필요하다.
- 프로젝트에서는 `harness-setup`을 호출해 `.ai-docs/**`, 루트 `AGENTS.md`, `CLAUDE.md`만 만든다.
- `harness-setup`은 사용자 프로젝트에 `.agents/skills/`, `.claude/skills/`, `skills/`를 생성하거나 스킬을 복사·동기화하지 않는다.
- 모든 참여자는 자기 작업 환경에서 `harness-setup`을 최초 1회 실행하고, 단일·복수 repo 구분 없이 `git-scoped-account`로 각 repo의 Git 작성자와 provider 계정을 등록한다.
- 문서 쓰기 권한을 나눌 때만 관리자가 `project-write-access`를 명시 호출해 공유 정책을 설정한다. 정책 생성 뒤에는 각 참여자가 관리자 키 없이 자기 PC의 로컬 Git·AI 가드를 등록한다. 권한 기능이 없어도 나머지 하네스 흐름은 그대로 사용할 수 있다.
- `.md` 산출물 후처리는 별도 `im-not-ai` 설치 없이 내장 `humanize-korean`을 쓴다.

---

## 2. 현재 stable 정보

| 항목 | 값 |
|------|----|
| Plugin ID | `harness-kit` |
| Version | `0.6.0` |
| Local plugin root | `plugins/harness-kit` |
| Archive | `plugins/harness-kit-0.6.0.zip` |
| Archive SHA-256 | `05254286fb1ed8266843230ae6839dbaeadd3088791adb660f17749204445a2f` |
| Codex physical skills | 20 |
| Codex agents | 0 |
| Claude physical skills | 20 |
| Claude agents | 0 |
| GitHub Release | [`v0.6.0`](https://github.com/hb9397/harness-kit/releases/tag/v0.6.0) |
| Candidate record | `maintainer/plugin/release.json` |
| Stable publication record | `maintainer/plugin/publish.json` |
| Release gate | `not-release-ready` — Codex·Claude CLI·앱의 실제 모델 호출 수동 증적이 모두 충족되지 않음 |

릴리스 게이트 증적은 [maintainer/plugin/release-checklist.md](../maintainer/plugin/release-checklist.md)와 [maintainer/plugin/install-verification.json](../maintainer/plugin/install-verification.json)에 있다.

관리 저장소의 사용자 스킬 정본과 `0.6.0`의 Codex·Claude runtime은 모두 20종이다. `project-write-access`도 stable에 포함되지만 자동으로 실행되지 않는다. 공유 정책 설정·변경은 검증된 관리자만 명시적으로 수행하고, 정책 생성 뒤의 PC별 로컬 등록은 각 참여자가 수행한다.

---

## 3. Codex CLI

> `0.6.0` stable의 Codex CLI와 Claude Code 격리 설치·cache smoke는 통과했다.
> 이 검사는 실제 모델 호출과 앱 설치·trust의 수동 증적을 대신하지 않는다.

공식 Codex CLI `0.146.0`을 임시 `CODEX_HOME`에서 실행해 아래 marketplace 등록·설치·목록·제거 흐름과 설치 cache의 skills / 0 agents를 확인했다.
CI도 같은 격리 smoke를 반복하고, 배포 전 실제 사용자 CLI에서 한 번 더 확인한다.

### 3-1. marketplace source 관리

Git-backed marketplace를 사용하는 경우:

```text
codex plugin marketplace add <github-owner/repo | git-url | 저장소-루트-경로>
codex plugin marketplace list
```

`marketplace add`에는 source 하나만 전달한다. Git ref를 고정하려면 `--ref`를 사용한다. 저장소 루트의 `.agents/plugins/marketplace.json`이 `hb9397` marketplace에서 `harness-kit` 플러그인을 노출한다.

업데이트는 marketplace를 갱신한 뒤 plugin을 재설치하는 방식으로 검증한다.

```text
codex plugin marketplace upgrade hb9397
codex plugin add harness-kit@hb9397
```

### 3-2. 비대화식 설치 관리

```text
codex plugin add harness-kit@hb9397
codex plugin list
codex plugin remove harness-kit@hb9397
```

설치 후 새 task를 열고 Codex 명시 호출인 `$harness-setup`, `$humanize-korean`이 동작하는지 확인한다. 자연어 요청은 별도 대조 항목으로 기록하며 명시 호출 성공을 대신하지 않는다.

### 3-3. Codex 앱의 대화형 설치

Codex 앱에서는 왼쪽 메뉴의 **플러그인**과 `/plugins` UI에서 설치·활성화·비활성화를 확인한다. CLI 설치와 앱 설치는 cache·활성 session이 다를 수 있으므로 둘을 별도 증적으로 남긴다.

### 3-4. Codex IDE extension

Codex IDE extension은 이 문서의 별도 플러그인 설치 인터페이스로 다루지 않는다. 프로젝트에서 확장이 Codex CLI/앱 플러그인 상태를 공유하지 않으면 `AGENTS.md`와 `.ai-docs` 산출물만 일반 프로젝트 문서로 참조한다.

---

## 4. Codex 앱

아래 화면은 Codex 앱에서 **플러그인 → 설정 → 플러그인 마켓플레이스 추가**를 연 예시다. 화면 이름은 앱 버전에 따라 달라질 수 있지만 저장소 source, Git ref, 선택적 sparse 경로를 입력한다는 흐름은 같다.

![Codex 앱의 플러그인 마켓플레이스 추가 화면](./assets/plugin-install/codex-app-add-marketplace.png)

Codex 앱에서는 다음을 수동으로 확인한다.

1. 왼쪽 메뉴에서 **플러그인**을 열고 설치 목록의 설정 아이콘을 누른다.
2. **플러그인 마켓플레이스 추가**에서 `hb9397/harness-kit` 저장소 또는 Git URL, `main` ref를 입력한다. monorepo 일부만 사용할 때만 sparse 경로를 지정한다.
3. 추가한 marketplace에서 `harness-kit`을 찾아 설치한다.
4. local marketplace가 앱에 보이지 않는 버전이면 앱과 같은 사용자 프로필의 Codex CLI에서 marketplace와 플러그인을 등록하고 앱을 완전히 종료했다가 다시 연다.
5. 플러그인 화면 또는 `/plugins`에서 `harness-kit` `0.6.0`이 설치·활성 상태인지 확인한다.
6. 새 fixture 프로젝트에서 새 task/session을 연다.
7. `$harness-setup`과 `$humanize-korean`을 명시 호출한다.
8. 새 버전 후보를 설치하거나 stale cache를 비운 뒤 version marker가 갱신되는지 확인한다.

앱 버전에 local marketplace를 직접 추가하는 UI가 없다면 위 CLI fallback을 사용하고, UI 직접 설치인지 CLI 설치 후 앱 사용인지 수동 증적에 구분해 기록한다.

자동 검증은 package와 CLI까지만 수행하며 Codex 앱 결과는 `manual-required`다. Codex 앱에서는 `$skill-name`, ChatGPT Work에서는 `@` mention을 사용하므로 이 릴리스의 Codex 앱 증적은 `$harness-setup`으로 남긴다.
ChatGPT Work를 추가 지원 범위로 검증하면 `@` 호출 결과를 별도 인터페이스 증적으로 기록한다.

---

## 5. Claude Code CLI

Claude Code `2.1.50`을 별도 `CLAUDE_CONFIG_DIR`과 plugin cache에서 실행해 아래 흐름과 설치 cache의 20 skills / 0 agents를 확인했다. CI도 같은 격리 smoke를 반복한다.

```text
claude plugin validate plugins/harness-kit
claude plugin validate .
claude plugin marketplace add <github-owner/repo | git-url | ./로-시작하는-로컬-상대경로>
claude plugin marketplace list
claude plugin install harness-kit@hb9397
claude plugin list
```

설치 후 `claude` 대화형 session 안에서 `/reload-plugins`를 실행한다.

업데이트와 제거:

```text
claude plugin marketplace update hb9397
claude plugin update harness-kit@hb9397
claude plugin uninstall harness-kit@hb9397
```

검증:

- namespaced `/harness-kit:harness-setup` 호출 가능
- namespaced `/harness-kit:humanize-korean` 호출 가능
- `.claude-plugin/plugin.json`의 version 확인
- `/reload-plugins` 후 새 skill 목록 확인

---

## 6. Claude 앱

아래 화면은 Claude 앱의 **설정 → 플러그인 → 추가 → 마켓플레이스 추가** 예시다. GitHub `owner/repo` 또는 Git 저장소 URL을 선택하고 동기화한다.

![Claude 앱의 마켓플레이스 추가 화면](./assets/plugin-install/claude-app-add-marketplace.png)

Claude 앱과 Claude Code CLI는 일부 설정을 공유할 수 있지만 host별 plugin cache와 활성 session을 따로 확인해야 한다.

1. **설정 → 플러그인**에서 **추가 → 마켓플레이스 추가**를 연다.
2. `hb9397/harness-kit` 또는 Git 저장소 URL을 선택하고 **동기화**한다.
3. 동기화된 marketplace에서 `harness-kit`을 설치한다.
4. local marketplace가 목록에 보이지 않으면 같은 사용자 설정의 Claude Code CLI에서 marketplace만 등록한 뒤 앱을 다시 열어 설치한다.
5. SSH host를 공식 지원 범위로 선언하는 릴리스라면 해당 remote host에서도 plugin cache와 설치를 별도로 확인한다.
6. 앱 재시작
7. 새 Code session
8. `/harness-kit:harness-setup`, `/harness-kit:humanize-korean` 명시 호출 확인
9. cloud Code session은 plugin browser가 없어 프로젝트 `enabledPlugins` 정책을 별도 적용
10. WSL session은 Desktop plugin 설치 인터페이스로 지원하지 않음을 명시

`0.6.0`은 annotated tag와 stable GitHub Release로 게시됐다. Codex·Claude CLI의 격리 설치 smoke는 통과했고, 앱 설치와 직접 모델 호출은 수동 검증 항목으로 남긴다.

---

## 7. Claude Chat/Cowork

Claude Chat/Cowork는 Claude Code 플러그인과 같은 설치 인터페이스로 취급하지 않는다.

- Code 탭에서 검증된 플러그인이 Chat/Cowork에서 자동 활성화된다고 가정하지 않는다.
- Chat/Cowork에서 같은 스킬을 쓰려면 별도 프로젝트/워크스페이스 지침, 권한, 파일 접근 범위를 문서화한다.
- 사용자가 Code와 Chat을 오가면 최종 기준 문서는 프로젝트의 `AGENTS.md`와 `.ai-docs`로 둔다.

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
플랫폼별 plugin marketplace upgrade/update hb9397
플랫폼별 plugin remove/uninstall harness-kit@hb9397
플랫폼별 plugin add/install harness-kit@hb9397
새 task/session
version marker 확인
```

---

## 9. 설치 후 첫 하네스 설정

플러그인을 설치한 뒤 프로젝트에서 다음 순서로 진행한다.

```text
harness-setup 명시 호출
→ 모든 참여자가 자기 작업 환경에서 최초 1회 수행
→ 단일/복수 앱 확인
→ .ai-docs 생성 또는 갱신
→ AGENTS.md 생성 또는 갱신
→ CLAUDE.md bridge 생성 또는 갱신
→ .agents/skills·.claude/skills·skills 미생성 확인
→ 단일·복수 repo: 모든 참여자가 자기 PC에서 git-scoped-account 최초 1회
→ 문서 권한을 분리하면 원격 Git provider·저장소·참여자 계정 준비
→ 관리자: project-write-access 공유 정책 설정
→ 모든 참여자: 현재 PC의 로컬 Git·AI 가드 등록
→ 권한 정책이 있으면 허용된 역할·앱 범위에서 design-doc/context-doc 또는 harness-bootstrap
→ 권한 정책이 없으면 같은 문서화 흐름을 그대로 수행
```

`harness-setup`은 플러그인 공지가 프로젝트 하네스 갱신을 요구하거나 앱 경계가 바뀌거나 골격 복구가 필요할 때만 update mode로 다시 실행한다. 서명 권한 정책이 활성화된 뒤 공유 루트·하네스 파일의 실제 갱신은 `admin`이 수행하고, 다른 참여자는 갱신된 파일과 자기 PC의 로컬 연결 상태를 확인한다. `git-scoped-account`는 새 PC·새 clone, 계정 변경 또는 컨테이너 바로 아래 repo 추가 때 다시 실행한다.

새 문서 루트는 `.ai-docs/` 하나뿐이다. 이전 `.docs/`만 있으면 일반 설정을 중단하고 이관 계획과 별도 승인을 거친다. 서명된 권한 정책이 있으면 `admin`이 `project-write-access`의 전용 이관 흐름으로 정책·Git 훅·AI 가드 경로를 함께 바꾼다. `.docs/`와 `.ai-docs/`가 함께 있으면 자동 병합하지 않는다.

`project-write-access`가 활성화되면 `pm-pl`은 모든 앱, `app-doc-lead`는 배정된 앱에서 `design-doc`과 `context-doc`을 사용한다. 두 역할이 AI로 앱 핵심 문서를 쓰기 전에도 대상 문서의 역할과 변경 이유를 설명받고 한 번 더 확인한다. `admin`은 앱 문서 권한을 상속하지 않고 루트 컨텍스트·하네스·권한 정책만 관리한다. `developer`는 일반 참여자를 명시하는 역할이며, 구현 계획·프로토타입·`_inbox` 같은 팀 문서와 애플리케이션 소스코드 작업은 기존 저장소 권한을 따른다. 정책이 있는데 현재 PC의 `git-scoped-account` 또는 로컬 등록이 없거나 계정이 다르면 지원되는 AI 가드는 `.ai-docs/**` 쓰기를 거부한다.

복수 앱에서는 `.ai-docs/root-context/AGENTS.md`가 루트 컨텍스트의 관리 원본이다. 루트 `CLAUDE.md`는 `AGENTS.md`를 읽도록 하는 bridge로 둔다.

플랫폼별 명시 호출:

| 플랫폼 | 호출 예 |
|---|---|
| Codex CLI·앱 | `$harness-setup` |
| Claude Code CLI·Claude 앱 | `/harness-kit:harness-setup` |

`0.6.0`에서 권한 기능을 명시 호출하는 방법은 Codex `$project-write-access`, Claude Code·Claude 앱 `/harness-kit:project-write-access`다. 최초 설정과 이후 공유 정책 변경은 검증된 관리자만 수행한다. 각 참여자의 PC별 로컬 등록은 `git-scoped-account`가 서명된 정책을 발견했을 때 별도 계획과 승인을 거쳐 `project-write-access`의 로컬 등록 분기로 연결한다.

---

## 10. Markdown 산출물 후처리

여기서 producer는 Markdown 파일이나 문서 묶음을 생성·갱신하고 저장 경로와 구조를 검증한 뒤 다음 단계로 넘기는 산출물 책임 스킬을 뜻한다. Markdown producer는 고정 7종과 조건부 2종, 총 9종이다.

고정 producer 7종:

- `harness-setup`
- `harness-bootstrap`
- `context-doc`
- `design-doc`
- `design-prototype-docs`
- `impl-doc`
- `impl-fe-be-doc`

조건부 producer 2종:

- `ui-ux-pro-max`
- `motion-design`

조건부 2종은 기본적으로 대화창에 결과를 보고하며 사용자가 디자인 시스템이나 모션 명세의 저장을 명시적으로 요청했을 때만 파일을 만든다. 모든 producer는 단일 앱의 `@.ai-docs/instruction/artifact-output-routing-instruction.md` 또는 복수 앱의 `@.ai-docs/{앱}/instruction/artifact-output-routing-instruction.md`에 따라 위치·소유권·인계를 결정한다.

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

## 11. 프로젝트 내부 사용자 스킬 복사본 처리

프로젝트에서는 사용자 스킬을 설치된 플러그인에서만 사용한다. `.agents/skills` 또는 `.claude/skills`에서 사용자 스킬 복사본을 발견하면 기본 동작은 삭제가 아니라 읽기 전용 inventory다.

분류:

- 플러그인 사용자 스킬 복사본
- 사용자가 수정한 복사본
- unknown custom skill

삭제 또는 이동은 다음 조건을 만족해야 한다.

1. 백업 대상 확인: `.ai-docs/archive/legacy-agent-skills/{timestamp}/`
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
| setup 후 새 skill 디렉터리가 생김 | 중단. `.ai-docs/**`, `AGENTS.md`, `CLAUDE.md` 출력 allowlist 위반으로 보고 |

---

## 13. CLI·앱 직접 테스트 예시와 증적

자동 CLI smoke는 설치 cache와 payload 수를 검증하지만 실제 agent가 `harness-setup`을 수행한 결과까지 대신하지 않는다. 릴리스 판단 전에는 각 인터페이스의 서로 다른 새 fixture 프로젝트에서 다음을 직접 확인한다.

1. 실제 플러그인 설치·활성 버전
2. 새 task/session에서 명시 호출
3. `.ai-docs/**`, `AGENTS.md`, `CLAUDE.md` 생성
4. `.agents/skills`, `.claude/skills`, `skills` 미생성
5. 재실행 시 managed block 밖 사용자 확장 보존
6. 새 task/session에서 같은 artifact fingerprint의 문서 개선안 재제안 없음
7. 실패·중단 시 기존 파일 보존

정확한 Codex CLI·앱, Claude Code CLI·Claude 앱 명령 예와 인터페이스별 증적 양식은 [Direct Plugin Surface Test Record](../maintainer/plugin/manual-surface-test-template.md)를 복사해 사용한다. 스크린샷만 남기지 말고 CLI/app 버전, plugin version, fixture 경로, 명시 호출, 생성 파일, 금지 경로 검사 출력과 검토자를 함께 기록한다.
중복 handoff 검증은 `.ai-docs/.harness/humanize-handoffs.json`의 event와 함께 남기며 이 JSON 자체는 Markdown 개선 대상에서 제외한다.
