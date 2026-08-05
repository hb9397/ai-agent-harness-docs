---
name: harness-setup
description: >
  harness-kit 플러그인이 설치된 프로젝트에 문서 하네스를 설정·갱신한다.
  '하네스 설정', '하네스 세팅', '프로젝트 세팅',
  '하네스 설치', 'setup', '초기 설정', '프로젝트 초기화',
  '하네스 갱신', '하네스 업데이트',
  'harness setup', 'harness init' 요청이 오면 이 스킬을 사용한다.
  단일/복수 애플리케이션 프로젝트를 판별하여 .docs 구조와 루트 Agent 컨텍스트를 세팅한다.
  사용자 스킬 설치·갱신은 harness-kit 플러그인이 담당하며, 이 스킬은 프로젝트 local skill copy를 만들거나 덮어쓰지 않는다.
allowed-tools: Read, Write, Glob, Grep
---

## 스킬 연계

```
harness-kit plugin
    ↓
harness-setup  ← 지금 여기
    ↓
프로젝트 .docs/ 구조 + AGENTS.md 정본 + CLAUDE.md bridge 세팅
    ↓
design-doc, context-doc 등 후속 스킬 사용 가능
```

---

## 책임 경계

이 스킬은 프로젝트 문서 하네스만 관리한다.

| 영역 | 처리 |
|------|------|
| 사용자 스킬 설치·업데이트 | `harness-kit` 플러그인 설치·업데이트가 담당 |
| 프로젝트 `.docs/` 구조 | harness-setup이 생성·갱신 |
| 루트 `AGENTS.md` | harness-setup이 공통 컨텍스트 정본의 뼈대를 생성·갱신하고, `context-doc`이 프로젝트 팩트와 instruction 인덱스를 보강 |
| 루트 `CLAUDE.md` | harness-setup이 `@AGENTS.md` bridge와 Claude 전용 delta만 생성 |
| `.agents/skills`, `.claude/skills`, `skills`의 사용자 스킬 local copy | 생성·동기화 금지. 기존 `*/SKILL.md`만 읽기 전용으로 보고 |

---

## 플러그인 리소스 해석 계약

이 스킬의 `templates/**`와 `prompts/**`는 프로젝트 경로가 아니라 **설치된
`harness-setup` 스킬 번들의 리소스**다.

1. 플랫폼이 현재 로드한 `harness-setup/SKILL.md`의 실제 위치 또는 번들 리소스
   핸들을 기준으로 같은 디렉토리의 `templates/{파일명}`을 읽는다.
2. 템플릿 내용을 먼저 읽고 대상 프로젝트 파일에 쓴다. shell copy가 필요하면
   플랫폼이 노출한 실제 절대 경로를 사용한다.
3. 현재 작업 디렉토리, 관리 저장소의 `skills/harness-setup`, 임의의 clone 경로를
   템플릿 원본으로 추측하지 않는다.
4. `[plugin:harness-setup]` 같은 의사 경로를 shell에 전달하지 않는다.
5. 번들 리소스를 읽을 수 없으면 내용을 기억으로 재구성하지 말고 설치 오류로
   보고한 뒤 쓰기를 중단한다.

---

## 사용자 프로젝트 불변조건

실행 전 변경 계획과 실행 후 실제 변경 목록을 모두 검사한다.

- 허용되는 생성·갱신 범위는 `.docs/**`, 루트 `AGENTS.md`, 루트 `CLAUDE.md`뿐이다.
  `@.docs/instruction/artifact-output-routing-instruction.md`(복수 앱은
  `@.docs/{앱}/instruction/artifact-output-routing-instruction.md`)는 산출물 위치·
  소유권·인계를 위한 공용 instruction으로 항상 포함한다.
- `.agents/skills/**`, `.claude/skills/**`, `skills/**`에 사용자 플러그인 스킬을
  생성·복사·동기화하지 않는다.
- 기존 local skill copy는 탐지와 읽기 전용 report만 허용한다. 삭제·이동·백업도
  이 스킬의 책임이 아니다.
- 변경 계획에 금지 경로가 포함되면 파일을 쓰기 전에 중단한다.
- 실행 후 변경 목록에 금지 경로가 나타나면 성공으로 보고하지 않고 위반 경로를
  명시한다. 실행 전에 존재하던 경로는 수정하거나 삭제하지 않는다.

---

## Step 0 — 플랫폼 및 실행 방식 확인

현재 플랫폼과 사용 가능한 실행 도구는 먼저 자동 감지한다. 이 작업은 파일 수가
적은 초기 세팅에서는 기본적으로 순차 실행한다. 복수 앱 탐색처럼 병렬 처리가
실질적으로 유리하고 현재 플랫폼이 지원할 때만 병렬 실행 여부를 사용자에게 묻는다.
플랫폼 이름을 사용자가 직접 맞히도록 요구하지 않는다.

---

## Step 1 — 실행 컨텍스트 감지

`prompts/detection.md`의 [실행 컨텍스트 감지] 섹션을 참조하여 아래를 판정한다:

| 감지 결과 | 의미 | 다음 동작 |
|-----------|------|-----------|
| 사용자 프로젝트 내부에서 실행 중 | 최초 세팅 또는 갱신 | **현재 위치**를 프로젝트 루트 후보로 설정 → Step 2 |
| 하네스 관리 레포 내부에서 실행 중 | 관리자 작업 위치 | 사용자에게 대상 프로젝트 루트 경로 질문 → Step 2 |
| 판별 불가 | — | 사용자에게 프로젝트 루트 경로를 직접 질문 |

감지 결과를 사용자에게 보여주고 **반드시 확인**받는다:

> "현재 `{감지된 경로}`를 프로젝트 루트로 인식했습니다. 맞습니까?"

---

## Step 2 — 프로젝트 유형 감지 (단일/복수 애플리케이션)

`prompts/detection.md`의 [프로젝트 유형 감지] 섹션을 참조한다.

판정 후 사용자에게 결과를 보여주고 **반드시 확인**한다:

> ✋ **확인 게이트 (C-1)**
>
> 탐색 결과:
> - 프로젝트 유형: **단일 애플리케이션** / **복수 애플리케이션**
> - 프로젝트 루트: `{경로}`
> - (복수인 경우) 감지된 애플리케이션 폴더:
>   - `{앱1 폴더명}` — {근거: package.json / pom.xml / ...}
>   - `{앱2 폴더명}` — {근거}
>   - ...
>
> 맞습니까? **(승인 / 수정 / 취소)**

---

## Step 3 — 초기 세팅 / 갱신 판별

`prompts/detection.md`의 [세팅 모드 판별] 섹션을 참조한다.

| 조건 | 모드 | 다음 |
|------|------|------|
| `.docs/`와 `AGENTS.md`가 모두 없음 | **초기 세팅** | Step 4 |
| `.docs/` 또는 `AGENTS.md` 중 하나 이상 존재 | **갱신/복구** | Step 5 |

판별 결과를 사용자에게 알린다:

> "기존 하네스가 **감지되지 않았습니다** / **감지되었습니다**. 초기 세팅 / 갱신을 진행합니다."

`.claude/skills/`, `.agents/skills/` 또는 프로젝트 루트 `skills/*/SKILL.md`가
발견되면 legacy/custom local skill 후보로만 기록한다. 이 단계에서
생성·수정·삭제하지 않는다. 일반 소스 디렉토리 `skills/`는 `SKILL.md`가 없으면
local skill copy로 분류하지 않는다.

---

## Step 4 — 초기 세팅

Step 2 확인 결과에 따라 분기한다.

### Step 4-A — 단일 애플리케이션 세팅

`prompts/single-app-setup.md` 참조.

핵심 작업:
1. `.docs/` 안내·정책 파일 생성: `.docs/README.md`(구조·산출물 안내), `.docs/.gitignore`(로컬 전용 영역 지정), `.docs/_inbox/`(에이전트 임시 입력 공간, 내용 git 미추적), `.docs/instruction/artifact-output-routing-instruction.md` 참조 위치 예약
2. 루트 `AGENTS.md`가 없으면 공통 컨텍스트 정본 뼈대 생성
3. 루트 `CLAUDE.md`가 없으면 `@AGENTS.md` bridge 생성
4. 기존 local skill copy가 있으면 읽기 전용 migration report만 출력

### Step 4-B — 복수 애플리케이션 세팅

`prompts/multi-app-setup.md` 참조.

핵심 작업:
1. 프로젝트 최상위 폴더에 구조 생성 (**이 폴더는 `git init` 하지 않는다**)
2. `.docs/` 디렉토리 생성 (별도 git 레포로 관리 예정)
3. 앱별 빈 컨텍스트 파일 생성: `.docs/{앱}-context.md`
4. 앱별 하위 구조 생성: `.docs/{앱}/instruction/`
5. `.docs/root-context/` 생성 (루트 컨텍스트 파일 복사본 보관용)
6. 루트 `AGENTS.md` 생성 (git 미관리, 이 스킬이 단독 관리)
7. 루트 `CLAUDE.md` bridge 생성 (git 미관리, 이 스킬이 단독 관리)
8. `.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md` 복사본 생성
9. `.docs/` 안내·정책 파일 생성: `.docs/README.md`(구조·산출물 안내), `.docs/.gitignore`(로컬 전용 영역 지정), `.docs/_inbox/`(에이전트 임시 입력 공간, 내용 git 미추적), 앱별 `artifact-output-routing-instruction.md` 참조 위치 예약

루트 `CLAUDE.md`/`AGENTS.md` 작성 시 `templates/root-context.template` 참조.

### Step 4 완료 보고

생성된 구조를 트리 형태로 사용자에게 보여준다.

> **세팅 완료!**
>
> 생성된 구조:
> ```
> {프로젝트 루트}/
> ├── .docs/
> │   ├── README.md           ← 구조·산출물 안내
> │   ├── .gitignore          ← 로컬 전용 영역 지정
> │   ├── _inbox/             ← 에이전트 임시 입력 공간 (내용 git 미추적)
> │   └── ...
> ├── CLAUDE.md
> └── AGENTS.md
> ```
>
> 📌 멀티플랫폼 안내:
> - 스킬은 프로젝트 local copy가 아니라 `harness-kit` 플러그인으로 사용합니다.
> - `AGENTS.md`는 공통 정본, `CLAUDE.md`는 `@AGENTS.md` bridge입니다.
> - `.agents/skills/`, `.claude/skills/`, `skills/`에는 사용자 스킬을 만들거나 동기화하지 않았습니다.

→ Step 6으로 이동.

---

## Step 5 — 갱신 모드

`prompts/update-mode.md` 참조.

핵심 작업:
1. `.docs/` 안내·정책 파일의 관리 블록만 최신 템플릿 기준으로 갱신
2. 루트 `AGENTS.md`와 `CLAUDE.md` bridge를 확인하고 사용자 확장을 보존하며 갱신
3. 기존 local skill copy가 있으면 읽기 전용 migration report를 출력
4. 복수앱인 경우 추가로:
   - `.docs/root-context/CLAUDE.md`, `.docs/root-context/AGENTS.md` 갱신
   - 루트 `CLAUDE.md`, `AGENTS.md` 를 `.docs/root-context/` 기준으로 갱신
5. 갱신 전 사용자 확인

> ✋ **확인 게이트**
>
> 갱신 대상:
> - `.docs` 안내·정책: {갱신 필요 / 변경 없음}
> - 루트 컨텍스트: {AGENTS 갱신 필요 / CLAUDE bridge 갱신 필요 / 변경 없음}
> - legacy local skill copy: {읽기 전용 report N건 / 없음}
> - (복수앱) 루트 컨텍스트: {갱신 필요 / 변경 없음}
>
> 진행하시겠습니까? **(승인 / 취소)**

→ Step 6으로 이동.

---

## Step 6 — 최종 결과 보고

세팅 또는 갱신 결과를 요약하여 대화창에 출력한다.
별도 `.md` 파일을 생성하지 않는다.

보고 항목:
1. 프로젝트 유형 (단일/복수)
2. 프로젝트 루트 경로
3. 생성·갱신된 파일 목록 (`.docs/README.md`, `.docs/.gitignore`, `.docs/_inbox/` 포함)
4. (복수앱) 감지된 애플리케이션 폴더 목록
5. `.docs/_inbox/`는 에이전트에게 읽힐 파일을 잠시 올려두는 로컬 전용 공간이며 내용은 git에 올라가지 않는다는 안내
6. 기존 local skill copy가 있으면 승인 전에는 변경하지 않았다는 안내
7. 금지된 local skill 경로를 생성·갱신하지 않았다는 실행 후 검증 결과
8. 다음 단계 안내

> **다음 단계:**
> - 설계 시작: `design-doc` 스킬
> - 기존 코드 분석: `harness-bootstrap` 스킬
> - 컨텍스트 문서 생성: `context-doc` 스킬
> - 하네스 갱신: `harness-setup` 스킬
>
> 명시 호출 예: Codex는 `$harness-setup`, Claude Code 플러그인은
> `/harness-kit:harness-setup`을 사용한다.

---

## 문서 개선 후처리와 bundle 소유권

이 스킬을 사용자가 직접 호출하면 쓰기 전에 다음 실행 컨텍스트를 만든다.

```text
artifact_bundle_id = harness-setup:{정규화한 프로젝트 루트}:{이번 실행의 고유 ID}
handoff_owner = harness-setup
suppress_child_handoff = false
handoff_completed = false
```

`artifact_bundle_id`의 고유 ID는 한 실행 안에서 부모·자식 workflow를 연결하는
correlation 용도일 뿐, 재실행 중복 방지 키로 사용하지 않는다.

다른 producer가 전달한 `artifact_bundle_id`가 있으면 새 ID를 만들지 않고 전달받은
값과 `handoff_owner`를 보존한다. 이 경우 이 스킬이 owner가 아니므로
`suppress_child_handoff = true`로 처리한다.

`AGENTS.md`, `CLAUDE.md`, `.docs/README.md` 등 이번 실행의 Markdown 산출물을 모두
검증한 뒤 다음 순서로 영속 handoff fingerprint를 만든다.

1. 프로젝트 루트 기준 상대경로로 정규화한 최종 Markdown 산출물 목록을 정렬한다.
2. 각 파일의 최종 내용 SHA-256을 계산한다.
3. `상대경로 + NUL + 내용 SHA-256` 행을 정렬된 순서로 결합한 canonical
   manifest의 SHA-256을 `artifact_fingerprint`로 사용한다.
4. ledger 파일 자체인 `.docs/.harness/humanize-handoffs.json`은 산출물 목록과
   humanize 대상에서 제외한다.

`.docs/.harness/humanize-handoffs.json`은 새 task/session에서도 중복 제안을
막는 영속 ledger다. 최소한 다음을 기록한다.

```text
schema_version
artifact_fingerprint
producer = harness-setup
artifact_bundle_id
profile = document-refinement
artifacts[] = {path, sha256}
events[] = {status, recorded_at}
```

status는 `proposed`, `skipped`, `rejected`, `applied`, `revalidated` 중 하나다.
같은 fingerprint에 이 status 중 하나가 이미 있으면 새 proposal을 만들지 않는다.
`proposed`면 기존 제안의 존재를 보고하고, `skipped`/`rejected`면 그 결정을
존중한다. `applied`인데 `revalidated`가 없으면 재제안하지 않고 원 producer
검증만 이어서 수행한다. 산출물 경로나 내용 hash가 바뀌면 새 fingerprint가 되어
새 제안 후보가 된다.

ledger는 sibling 임시 파일에 전체 JSON을 쓴 뒤 flush하고 원자적 replace한다.
쓰기 직전 기존 ledger hash가 읽을 때와 달라졌으면 다시 읽어 fingerprint별
event를 merge하고 재시도한다. ledger를 안전하게 기록할 수 없으면 proposal을
새로 제시하지 않고 오류를 보고한다. ledger는 Markdown이 아니며
`humanize-korean`에 전달하지 않는다.

다음 조건을 전부 만족하고 ledger에 같은 fingerprint가 없을 때만 bundle 전체에
대해 `humanize-korean`의 `document-refinement` 프로필을 **한 번** 제안한다.

- `handoff_owner == harness-setup`
- `suppress_child_handoff == false`
- `handoff_completed == false`

제안이 만들어지면 사용자에게 보여주기 전에 `proposed` event를 원자적으로
기록한다. 사용자가 건너뛰거나 거절하면 `skipped` 또는 `rejected`, 승인 적용하면
기존 fingerprint에 `applied`를 기록한다. 적용으로 파일 내용이 바뀌면 최종
산출물 hash로 fingerprint를 다시 계산하고 `supersedes_fingerprint`에 기존
fingerprint를 연결한 새 record에도 `applied`를 기록한다. 원 producer
재검증까지 통과하면 **적용 후 최종 fingerprint**에 `revalidated` event를
추가한다. 따라서 다음 session은 적용 후 내용을 새 후보로 오인하지 않는다.
실행 내에서는 결과와 관계없이 `handoff_completed = true`로 기록한다. 기본은
개선안 제안만 수행하며 사용자 승인 전에는 산출물 파일을 덮어쓰지 않는다. 제목,
표, 경로, 명령어, ID, 숫자, 날짜, 의무 수준 표현과
`harness-kit:managed:start/end` marker는 원문 그대로 보존한다.

---

## Portable routing lifecycle (Track B)

`harness-setup`은 `.docs/harness/artifact-routing.json`이 있으면 Layer 1의
`AGENTS.md`/`CLAUDE.md`에서 routing manifest와 앱별 routing instruction을 참조한다.
기존 bundle은 있으나 host adapter/config가 없거나 `uninstalled`이면 **manual portable
adoption**으로 분류한다. initial, update, recovery, manual portable adoption 결과는
host별 current/proposed diff, created/modified/unchanged, local-only/shared 파일과 trust
상태를 나누어 사용자에게 보인다.

기본 생성·갱신 범위는 `.docs/**`, 루트 `AGENTS.md`, 루트 `CLAUDE.md`다. G10으로
host 설치가 별도 승인된 실행에서만 `.claude/settings.json`,
`.claude/hooks/claude-pre-tool-use.ps1`, `.codex/hooks.json`,
`.codex/hooks/codex-pre-tool-use.ps1`의 관리 hook entry와 adapter를 다룬다. Claude
settings merge와 Codex hooks.json merge는 서로 다른 adapter이며 기존 사용자 설정은
보존한다.

`.docs/harness/install-routing.ps1`의 `-Plan`과 `-Check`은 읽기 전용이다. `-Apply`와
`-Uninstall`은 host별 diff를 확인한 별도 G10 승인 뒤에만
`-ApproveHostInstall`과 함께 실행한다. Codex 신규·변경 hook은 `/hooks` 검토·신뢰
증적 전까지 `pending-trust`이며 active로 보고하지 않는다. 생성된 project-owned
bundle과 활성화된 host hook이 모두 남은 범위에서만 setup manifest에
`harness-kit-runtime-required=false`를 기록한다.

사용자가 host의 실제 신뢰 검토를 마친 증적을 제시할 때만 `-ActivateTrust`와
`-ApproveTrustEvidence`로 해당 host의 manifest 상태를 `active`로 기록한다. 이 명령은
`/hooks`를 대신 실행하거나 신뢰를 자동 추론하지 않는다. 외부 text artifact는
`normalize-artifact.ps1 -Plan`으로 UTF-8·marker-aware merge proposal을 만들고 G12 승인 뒤
`-Promote -ApprovePromotion`으로 반영한다. JSON/YAML·이미지·PDF는 `_inbox` manifest만
갱신하며 lossless 여부를 알 수 없는 자동 canonical promotion은 금지한다.

host adapter가 활성화된 경우 공통 write guard는 absolute/relative, separator, case,
traversal을 정규화해 project containment를 확인한다. 기존 canonical file, 승인된 app
source, `.docs/_inbox/**`, manifest exception은 허용한다. 새 managed `.docs` 또는 root
context 파일은 target path·operation·content SHA-256·TTL에 정확히 묶인 one-shot marker가
있을 때만 통과하며 성공 후 원자적으로 소비한다. Codex는
`hookSpecificOutput.permissionDecision=deny`, Claude는 exit 2/stderr로 차단한다.

동적 Bash target, hosted tool, opt-out tool path, command 이후 redirect, 외부 process는
완전 판정할 수 없으므로 bypass evidence로 남긴다. 이를 전면 보안 sandbox나 Codex trust
자동 승인으로 설명하지 않는다.
