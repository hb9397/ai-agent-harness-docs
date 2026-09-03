# 플러그인 인터페이스 직접 검증 기록

> 목적: 로컬 릴리스 후보를 실제 Codex CLI, Codex 앱, Claude Code CLI,
> Claude 앱에서 설치하고 스킬을 호출한 증적을 남긴다.
> 이 문서는 실행 예시 겸 기록 양식이다. 테스트할 때 사본을 만들고
> `<...>` placeholder를 실제 값으로 바꾼다.

## 공통 원칙

- 네 인터페이스는 서로 다른 새 fixture 프로젝트에서 검사한다. 한 인터페이스의
  산출물을 다른 인터페이스가 재사용하면 discovery와 최초 설정 검증이 무효가 된다.
- fixture에는 최소한의 앱 manifest 하나만 둔다. 예:
  `{"name":"harness-surface-fixture","private":true}`인 `package.json`.
- 설치 source는 테스트한 관리 저장소의 절대 경로를 기록한다.
- 인증 토큰, 사용자 홈 경로의 비밀값, private URL query는 증적에서 마스킹한다.
- 각 인터페이스에서 초기 설정과 갱신을 모두 실행한다.
- 성공 판정에는 설치 목록뿐 아니라 실제 `harness-setup` 호출, 생성 파일,
  금지 디렉터리 미생성, 사용자 확장 보존이 모두 필요하다.
- 자동 설치 smoke와 실제 모델 호출은 별도 증적이다. CLI도 설치 smoke만으로
  `verified`로 기록하지 않는다.
- 완료한 사본은
  `maintainer/plugin/manual-evidence/YYYYMMDD/{surface}.md`에 저장하고,
  `maintainer/plugin/release-checklist.md`의 해당 인터페이스에 링크한다. 검토자 확인
  전에는 릴리스 상태를 `verified`로 바꾸지 않는다.

## 공통 시나리오

### A. 최초 설정

1. 비어 있는 fixture 프로젝트에 앱 manifest 하나를 만든다.
2. 해당 인터페이스에서 플러그인을 설치·활성화하고 새 task/session을 연다.
3. `harness-setup`을 명시 호출한다.
4. 단일 애플리케이션 판정과 fixture 루트를 승인한다.
5. 다음 파일을 확인한다.

```text
.ai-docs/README.md
.ai-docs/.gitignore
.ai-docs/_inbox/README.md
.ai-docs/_inbox/.gitkeep
AGENTS.md
CLAUDE.md
```

6. 다음 경로가 생성되지 않았음을 확인한다.

```text
.agents/skills
.claude/skills
skills
```

PowerShell 확인 예:

```powershell
@(
  '.agents/skills',
  '.claude/skills',
  'skills'
) | ForEach-Object { [pscustomobject]@{ Path = $_; Exists = Test-Path $_ } }
```

세 항목의 `Exists`가 모두 `False`여야 한다.

POSIX shell 확인 예:

```sh
for path in .agents/skills .claude/skills skills; do
  if [ -e "$path" ]; then
    printf 'FORBIDDEN_EXISTS %s\n' "$path"
  else
    printf 'ABSENT %s\n' "$path"
  fi
done
```

### B. 갱신과 사용자 확장 보존

1. `.ai-docs/README.md`의
   `<!-- harness-kit:managed:end -->` 뒤에 `TEAM-README-SENTINEL`을
   추가한다.
2. `AGENTS.md`의 관리 블록 뒤에 `TEAM-AGENT-SENTINEL`을 추가한다.
3. `CLAUDE.md`의 관리 블록 뒤에 `TEAM-CLAUDE-SENTINEL`을 추가한다.
4. 같은 인터페이스에서 `harness-setup`을 다시 실행하고 관리 블록 diff를 승인한다.
5. 세 sentinel이 그대로 남고 관리 블록만 갱신됐는지 확인한다.
6. 쓰기 전후에 `.agents/skills`, `.claude/skills`, `skills`가 계속 없음을
   다시 확인한다.

marker가 없는 구버전 파일을 시험할 때는 자동 overwrite가 일어나지 않고 diff와
merge/backup 선택지가 제시되는지 확인한다. 전체 교체를 승인하지 않은 상태에서는
원본 hash가 같아야 한다.

### C. 새 session 중복 handoff 방지

1. 문서 개선안을 한 번 제안받고 승인·거절·건너뜀 중 하나를 완료한다.
2. `.ai-docs/.harness/humanize-handoffs.json`에 최종 산출물 상대경로·내용 hash와
   해당 event가 기록됐는지 확인한다.
3. task/session을 완전히 닫고 같은 fixture에서 새 session을 연다.
4. 산출물을 변경하지 않은 채 `harness-setup`을 다시 실행한다.
5. 같은 fingerprint에는 새 개선안을 만들지 않고 기존 ledger 결정을 보고하는지
   확인한다.
6. Markdown 산출물 하나를 실제로 변경한 뒤 다시 실행해 새 fingerprint로
   처리되는지 확인한다.

ledger JSON 자체는 `humanize-korean`의 대상 파일 목록에 들어가면 안 된다.

### D. 중단 시 원본 보존

1. `.ai-docs/README.md`, `AGENTS.md`, `CLAUDE.md`의 hash를 기록한다.
2. marker 하나가 누락된 구버전 파일 fixture를 별도로 준비한다.
3. `harness-setup`이 overwrite 대신 diff와 merge/backup 선택지를 제시하는지
   확인하고, 쓰기 직전에 취소한다.
4. 세 원본 hash와 사용자 sentinel이 그대로인지 확인한다.
5. 실제 쓰기 실패를 재현했다면 생성된 임시 파일이 남지 않고, backup이 만들어진
   경우 복구 가능한지 확인한다. 실패를 인위적으로 만들지 못했으면 `not-tested`와
   이유를 기록하고 성공으로 간주하지 않는다.

### E. 디자인 결정 — 무저장 기본값

1. fixture에 기존 디자인 토큰이 있는 상태와 없는 상태를 각각 준비한다.
   토큰 예: `:root { --brand: #0D47A1; }`를 담은 CSS 파일 하나.
2. `ui-ux-pro-max`를 명시 호출하고 **파일을 만들지 말라고** 지시한다.
3. 확인한다.
   - 스킬이 프로젝트 유형과 대상 앱을 재확인했는가
   - 스택을 임의로 가정하지 않고 탐지했거나 물었는가
   - 기존 토큰이 있을 때 그 값을 우선했는가
   - 추천 근거를 제시했는가
   - **파일을 하나도 만들지 않았는가**
4. fixture 트리 hash를 호출 전후로 비교해 변화가 없음을 확인한다.

### F. 디자인 시스템 저장 — 승인과 거절

1. E에 이어 저장을 명시적으로 요청한다.
2. `.ai-docs/design-system/{slug}/MASTER.md`에만 생성되는지 확인한다. 다른 경로에
   파일이 생기면 실패다.
3. 같은 요청을 다시 보내 **기존 파일을 무승인 덮어쓰지 않는지** 확인한다.
   diff나 확인 요청 없이 덮어쓰면 실패다.
4. 저장을 거절하는 경로도 실행해 파일이 만들어지지 않는지 확인한다.
5. 별도 문체 개선 요청이 없을 때 `humanize-korean` 제안이 나오지 않는지 확인한다.
   이어 문체 개선을 명시 요청하면 최외곽 producer의 개선 제안이 **한 번만** 나와야
   한다. 색상 hex와 토큰 이름이 개선으로 바뀌면 실패다.

### G. 모션 — 생략과 설계

1. 정적 목록 화면을 주고 `motion-design`을 호출한다. 스킬이 **모션을 생략하고
   그 이유를 보고하는지** 확인한다. 목적 없는 모션을 제안하면 실패다.
2. 결제 버튼의 loading → success → error 전환을 요청한다. 확인한다.
   - 목적을 먼저 분류했는가
   - duration, easing, 사용할 속성을 제시했는가
   - **reduced-motion 대체안**이 포함됐는가. 단순히 "애니메이션 제거"로 끝내지
     않고 정보 전달 대체 수단을 적었는가
   - 정지 상태를 함께 설계했는가
3. 의료 예약 화면처럼 저밀도가 기본인 맥락을 주고 모션 밀도가 낮아지는지
   확인한다.
4. 레이아웃 유발 속성을 쓰겠다고 하면 **근거와 성능 검증 방법**을 함께
   제시하는지 확인한다.

### H. 두 분기 경계

1. "프로토타입만 필요하다"로 요청해 `.ai-docs/prototype/**`에만 산출물이 생기고,
   제품 소스 디렉터리가 변하지 않는지 확인한다.
2. 이어서 "이제 실제 화면으로 구현해달라"고 요청한다. 확인한다.
   - 프로토타입 HTML을 **복사하지 않고** 제품 구조에 맞게 다시 구현하는가
   - 기존 컴포넌트·토큰을 먼저 조사하는가
3. 새 fixture에서 처음부터 실제 화면 구현을 요청해 `create-prototype`을
   **강제하지 않는지** 확인한다.
4. 두 경로 모두 `impl-verify`로 연결되는지 확인한다.
5. 스킬이 다른 스킬의 내부 파일 경로를 읽으려 시도하면 실패로 기록한다.
   연결은 공개 스킬 이름으로만 이뤄져야 한다.

## Codex CLI 예시

```text
codex --version
codex plugin marketplace add <관리-저장소-절대경로>
codex plugin marketplace list
codex plugin add harness-kit@hb9397
codex plugin list
cd <codex-cli-fixture>
codex
```

새 Codex task에서:

```text
$harness-setup
$humanize-korean
```

두 번째 호출에는 `.ai-docs/README.md`를 대상으로 `document-refinement` 개선안만
제시하고 원본은 적용하지 말라고 요청한다.

자연어 대조 호출도 한 번 확인한다.

```text
이 프로젝트의 문서 하네스를 설정해줘.
```

디자인 흐름은 다음 호출로 시나리오 E~H를 검사한다.

```text
$ui-ux-pro-max
기존 React 관리자 화면의 디자인 시스템을 제안해줘.
현재 토큰이 있으면 우선하고 파일은 아직 만들지 마.
```

```text
$motion-design
이 결제 버튼의 loading → success → error 전환을 설계해줘.
reduced-motion 대체안과 성능 검증 기준도 포함해줘.
```

```text
$motion-design
이 정적 공지 목록 화면에 모션이 필요한지 판단해줘.
```

종료 후 공통 시나리오 A·B·C·D·E·F·G·H를 검사하고, 테스트가 끝나면
`codex plugin marketplace list`에서 marketplace 이름
`harness-kit`를 다시 확인한 뒤:

```text
codex plugin remove harness-kit@hb9397
codex plugin marketplace remove hb9397
```

## Codex 앱 예시

![Codex 앱의 플러그인 마켓플레이스 추가 화면](../../.user-docs/assets/plugin-install/codex-app-add-marketplace.png)

1. ChatGPT 데스크톱 앱 전환기에서 **Codex**를 선택하고 Plugins Directory를
   연다.
2. configured marketplace에 `harness-kit`가 보이면 상세 화면의 설치
   버튼으로 직접 설치한다.
3. local marketplace가 앱에 보이지 않으면 같은 사용자 프로필의 Codex CLI에서
   위 local marketplace와 플러그인을 등록하고 앱을 완전히 종료했다가 다시 연다.
4. Plugins Directory 또는 `/plugins`에서 `harness-kit`가 설치·활성
   상태인지 확인하고 설치 경로가 UI 직접 설치인지 CLI fallback인지 기록한다.
5. `<codex-app-fixture>`를 작업 폴더로 새 task를 연다.
6. `$harness-setup`과 `$humanize-korean`을 각각 명시 호출해 공통 시나리오
   A·B·C·D를 수행하고, `$ui-ux-pro-max`와 `$motion-design`으로 E·F·G·H를
   수행한다. `humanize-korean`은 `.ai-docs/README.md`의 개선안만
   제시하고 원본을 적용하지 않게 한다.
7. 플러그인 ID·버전 화면, 두 호출 화면, 최종 파일 트리, 금지 경로 확인 결과를
   캡처한다.

앱 UI가 local marketplace 자체를 추가하지 못하는 버전에서는 CLI 등록 후 앱을
재시작하는 흐름을 사용하고 그 사실을 증적에 기록한다.
Codex 앱의 스킬 명시 호출은 `$skill-name`이다. ChatGPT Work에서 확인하는
`@` plugin/skill mention은 별도 보조 인터페이스로 기록하고 이 Codex 앱 항목을
대체하지 않는다.

## Claude Code CLI 예시

다음 두 `validate` 명령은 관리 저장소 루트에서 실행한다.

```text
claude --version
claude plugin validate plugins/harness-kit
claude plugin validate .
cd <관리-저장소-부모-경로>
claude plugin marketplace add ./<관리-저장소-디렉터리명>
claude plugin marketplace list
claude plugin install harness-kit@hb9397
claude plugin list
cd <claude-cli-fixture>
claude
```

새 Claude Code session에서:

```text
/harness-kit:harness-setup
/harness-kit:humanize-korean
```

두 번째 호출에는 `.ai-docs/README.md`를 대상으로 `document-refinement` 개선안만
제시하고 원본은 적용하지 말라고 요청한다.

필요하면 `/reload-plugins` 후 다시 호출한다. 자연어 대조 호출도 한 번 확인한다.

```text
이 프로젝트의 문서 하네스를 설정해줘.
```

디자인 흐름은 다음 호출로 시나리오 E~H를 검사한다.

```text
/harness-kit:ui-ux-pro-max
의료 예약 화면의 접근성 중심 디자인 시스템을 제안해줘.
```

```text
/harness-kit:motion-design
모달 열기/닫기 동작을 설계하고 motion 감소 환경을 포함해줘.
```

종료 후 공통 시나리오 A·B·C·D·E·F·G·H를 검사하고, 테스트가 끝나면
`claude plugin marketplace list`에서 marketplace 이름
`harness-kit`를 다시 확인한 뒤:

```text
claude plugin uninstall harness-kit@hb9397
claude plugin marketplace remove hb9397
```

## Claude 앱 예시

![Claude 앱의 마켓플레이스 추가 화면](../../.user-docs/assets/plugin-install/claude-app-add-marketplace.png)

1. Claude 앱의 **설정 → 플러그인 → 추가 → 마켓플레이스 추가**에서
   `hb9397/harness-kit` 또는 Git 저장소 URL을 선택하고 동기화한다.
2. local marketplace가 보이지 않으면 같은 사용자 설정을 쓰는 Claude Code CLI로
   marketplace만 등록한 뒤 앱을 다시 열고, 앱의 Add plugin에서 설치한다.
3. Claude 앱을 완전히 종료했다가 다시 열고 Code 탭에서 새 local session을
   만든다.
4. `<claude-desktop-fixture>`를 열고
   `/harness-kit:harness-setup`과
   `/harness-kit:humanize-korean`을 각각 호출한다. 두 번째 호출은
   `.ai-docs/README.md`의 개선안만 제시하고 적용하지 않게 한다.
5. 공통 시나리오 A·B·C·D를 수행하고, `/harness-kit:ui-ux-pro-max`와
   `/harness-kit:motion-design`으로 E·F·G·H를 수행한다.
6. local host 외에 SSH host 지원을 릴리스 범위로 주장하려면 SSH host에도
   플러그인을 별도로 설치하고 새 fixture로 같은 검사를 반복한다.
7. cloud Code 또는 WSL처럼 검증하지 않은 host는 `verified`로 합치지 않고
   별도 `not-tested` 또는 `unsupported`로 기록한다.

## 인터페이스별 증적 기록

아래 블록을 인터페이스마다 복사해 작성한다.

```text
Surface: <codex-cli | codex-desktop-app | claude-code-cli | claude-desktop-code>
Status: <verified | failed | blocked | not-tested>
Tester:
Tested at / timezone:
OS / architecture:
Host type: <local | ssh | other>
CLI or app version:
Plugin ID / version:
Marketplace source type: local-path
Marketplace source:
Installation route: <CLI | app UI | CLI marketplace + app UI | CLI fallback>
Fresh fixture path:
Install/list evidence:
Explicit invocation used:
Natural-language invocation result:
Detected project type:
Created/updated files:
Forbidden directory check output:
Managed-block sentinel preservation:
Cross-session fingerprint / ledger result:
Plugin/version screenshot or transcript:
Harness invocation screenshot or transcript:
Humanize invocation/proposal-only result:
Design invocation (ui-ux-pro-max) result:
Motion invocation (motion-design) result:
Motion skip decision on a static screen:
Design-system save path and overwrite-guard result:
Prototype / real-screen branch result:
Failure/rollback notes:
Evidence file:
Sensitive values redacted: <yes/no>
Reviewer:
Reviewed at:
Final decision:
```

## 완료 판정표

| 확인 항목 | Codex CLI | Codex 앱 | Claude Code CLI | Claude 앱 |
|---|---|---|---|---|
| 설치·활성 버전 확인 | ☐ | ☐ | ☐ | ☐ |
| 새 task/session에서 스킬 발견 | ☐ | ☐ | ☐ | ☐ |
| `harness-setup` 명시 호출 성공 | ☐ | ☐ | ☐ | ☐ |
| `humanize-korean` 명시 호출·proposal-only 확인 | ☐ | ☐ | ☐ | ☐ |
| `ui-ux-pro-max` 명시 호출·무저장 기본값 확인 | ☐ | ☐ | ☐ | ☐ |
| `motion-design` 명시 호출·모션 생략 판단 확인 | ☐ | ☐ | ☐ | ☐ |
| 디자인 시스템 저장 경로·무승인 덮어쓰기 차단 | ☐ | ☐ | ☐ | ☐ |
| reduced-motion 대체안 포함 확인 | ☐ | ☐ | ☐ | ☐ |
| 프로토타입 코드 제품 소스 미승격 | ☐ | ☐ | ☐ | ☐ |
| 공개 skill-name handoff만 사용 | ☐ | ☐ | ☐ | ☐ |
| 자연어 호출 결과 기록 | ☐ | ☐ | ☐ | ☐ |
| 최초 설정 파일 6종 확인 | ☐ | ☐ | ☐ | ☐ |
| local skill 디렉터리 3종 미생성 | ☐ | ☐ | ☐ | ☐ |
| 갱신 시 사용자 sentinel 보존 | ☐ | ☐ | ☐ | ☐ |
| 새 session에서 동일 fingerprint 재제안 없음 | ☐ | ☐ | ☐ | ☐ |
| 실패 시 원본·fixture 복구 확인 | ☐ | ☐ | ☐ | ☐ |
| 증적 검토자 확인 | ☐ | ☐ | ☐ | ☐ |

네 인터페이스의 필수 항목이 모두 확인되기 전에는 앱을 포함한 전체 설치 검증을
`verified`로 기록하지 않는다.
