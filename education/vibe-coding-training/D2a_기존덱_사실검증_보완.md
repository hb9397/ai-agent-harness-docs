# ②덱(기존 14장) 사실 검증 · 보완 목록 (D2a)

> 대상: `AI_Agent_활용을 위한 개념.pptx` (14장). 과거 팀 공유본 → 웹 검증 후 교정·보완.
> 검증일: 2026-07-09

---

## A. 사실 검증 결과

| 슬라이드 | 기존 주장 | 판정 | 조치 |
|----------|-----------|------|------|
| 8 | "2026.01.24 (v2.1.3) — Slash Commands가 Skills로 통합" | **개념 ✅ / 버전·날짜 ⚠️** | 통합 사실은 맞음(`.claude/commands/*.md`와 `.claude/skills/*/SKILL.md` 둘 다 `/명령어` 생성, commands는 계속 작동, skills가 권장). **정확한 "v2.1.3 / 2026.01.24"는 확인 불가** → 구체 버전·날짜 삭제 또는 "2.1대에서"로 완화 |
| 11 | "Plugin 2025년 10월 출시" | **✅ 정확** | 유지 (원하면 "2025년 10월 9일"로 샤프닝) |
| 11 | "MCP — Anthropic 발표" | **✅ 정확** (2024-11) | 유지 |
| 8·13 | Codex `.codex/skills/` = "레거시 지원 (Conflict 주의)" | **❌ 부정확** | `.codex/skills/`는 **현행 프로젝트 레벨 경로**(레거시 아님). Codex는 `.agents/skills`를 cwd→repo root까지 스캔 + `~/.codex/skills/`(유저)·`.codex/skills/`(프로젝트)·`/etc/codex/skills`(관리자) 모두 지원. → "레거시" 표현 제거, "`.agents/skills/` = 교차도구 공용 표준, `.codex/skills/` = Codex 전용 프로젝트 경로"로 정정 |
| 8·13 | Antigravity `.agent/skills/*/SKILL.md` (단수) | **⚠️ 부정확(IDE 기준)** | **Antigravity IDE 프로젝트 경로는 `.agents/skills/` (복수)**. 전역은 `~/.gemini/config/skills/`. `.agent/` (단수)는 **Antigravity CLI** 경로. 덱은 "IDE 단독 환경"을 말하므로 **`.agents/skills/` (복수)로 정정** + IDE/CLI 차이 각주 |
| 8 | Antigravity workflows `.agent/workflows/` | **⚠️ 미확정** | IDE는 `.agents/`(복수) 계열일 가능성 높음 → `.agents/workflows/`로 추정 수정하되 **공식 확인 표시** |
| 9 | Gemini 커맨드 TOML에 `execute = ".agents/skills/multi-review"` 필드 | **❌ 부정확** | Gemini CLI 커스텀 커맨드 TOML 표준 필드는 **`prompt`·`description`뿐**. `execute` 필드는 없음. 스킬 호출은 `prompt` 본문에서 경로를 지시. 위치도 `~/.gemini/commands/`(전역) 또는 `<project>/.gemini/commands/`(프로젝트). → `execute` 줄 삭제, prompt 기반 예시로 교체 |
| 12 | Subagent 도구별 (Claude 🟢 / Codex·Gemini 🟡 / Antigravity 🔴) | **대체로 타당** | 환경별 상이 + Antigravity Browser Subagent 내장·커스텀 제한 = 대체로 맞음. 유지(경미) |
| 12 | Subagent YAML "model 필드 하드코딩 금지" | **✅ + 레포 규칙과 일치** | 유지 · **강조 포인트로 살릴 것** |

### 교정 우선순위
1. **높음(오정보)**: Codex `.codex/skills/` "레거시" 표현, Gemini `execute` 필드, Antigravity `.agent`(단수) 경로
2. **중간(과도한 구체성)**: Claude "v2.1.3 / 2026.01.24" → 완화
3. **낮음(확인 표시)**: Antigravity workflows 경로

---

## B. 맥락상 보충해야 할 내용 (교육 주장과의 연결)

사실 교정과 별개로, ②덱이 §1 관통 주장("결국 문서 쓰기")을 실증하려면 아래 맥락이 보충돼야 한다.

### B-1. 도입부 — ①덱과의 연결 (신설 1장)
- ②덱 맨 앞에 "①에서 말한 그 **문서**가 실제로 이 부품들이다" 연결 슬라이드.
- 기존 Slide 2(실행 흐름 `USER→Skills→Agent`)와 **층위 구분**: Slide 2 = 기계가 도는 흐름, ①덱 흐름 = 사람이 일을 시키는 흐름.

### B-2. `.md` 공통 규격 클라이맥스 (신설 1장) ⭐
- 지금 Slide 13(표)·14(takeaway)에 **흩어져만 있는** "플랫폼 공통 규격" 메시지를 **명시적 절정 1장**으로.
- **결정적 근거 추가**: **SKILL.md는 Anthropic·OpenAI·Google·Microsoft·Cursor가 함께 채택한 오픈 표준** — "하나의 스킬 파일이 20개 이상 에이전트에서 동작". 이는 §1 주장("한 번 익히면 어디서나 통한다")의 **가장 강한 증거**이므로 반드시 넣는다.
- `CLAUDE.md`/`AGENTS.md`/`GEMINI.md`도 마찬가지로 **AI Docs 공용 규격 수렴** 맥락으로 묶는다. (특히 `AGENTS.md`는 OpenAI 및 다수 도구 공용)

### B-3. 용어 통일
- 기존 덱 `Context / Instruction / Rule` ↔ 레포 `context-base / instruction`. 틀린 분류는 아니나 ③덱 실물과 흔들리지 않게 **한쪽으로 통일**.

### B-4. "부품 나열"에서 "주장 실증"으로 프레이밍 전환
- ②덱은 부품 도감이지만, 각 부품 설명 끝에 "**→ 결국 다 `.md`**"를 반복 각인시키는 미세 카피 추가 권장(AI Docs=.md, Skills=SKILL.md, Commands=.md/.toml, Hooks=스크립트+.md 정리 등).

---

## D. Gemini → Antigravity 통일 (검증 완료) + 최신 공식 경로

### D-1. 검증 결과 — 통합은 사실
- **Google 공식**: "Transitioning Gemini CLI to Antigravity CLI". **2026-06-18부로 개인/Pro/Ultra 대상 Gemini CLI·Gemini Code Assist IDE 확장 서비스 종료**(오늘 기준 이미 경과). Antigravity CLI가 후속이며 **Antigravity 2.0 데스크톱 앱과 동일 agent harness 공유**(Go 단일 바이너리, 멀티에이전트, 멀티모델).
- **예외(각주 필수)**: **엔터프라이즈**(Gemini Code Assist Standard/Enterprise, Google Cloud 경유 GitHub)는 **계속 지원**. → "Gemini 완전 소멸"은 과장이고, **"개인 개발 흐름은 Antigravity로 통일 중"**이 정확한 표현.
- **상충 주의**: 일부 자료(2026-02-05 Google Cloud 블로그)는 "둘이 공존"이라 하나 이는 **전환 발표(5월)·종료(6/18) 이전** 정보 → 최신(전환) 기준으로 판단.

### D-2. 최신 공식 Antigravity 구조 (기존 Gemini 칸을 이걸로 대체)
Antigravity는 `.agents/`를 네이티브 인식하는 특수 디렉토리로 쓴다:

| 구성요소 | 경로/파일 |
|----------|-----------|
| 진입·컨텍스트 문서 | `.agents/agents.md` (교차도구 표준 `AGENTS.md`와 같은 계열) |
| Skills | `.agents/skills/*/SKILL.md` |
| Workflows (= 슬래시 커맨드) | `.agents/workflows/*.md` |

> 이로써 앞선 A절의 Antigravity `.agent`(단수)·Gemini `.gemini/commands` 관련 항목은 **본 D절 최신 경로로 대체**된다.
>
> ⚠️ **workflows 경로 최종 확정 필요**: skills·agents.md는 `.agents/`(복수)로 수렴하나, workflows는 자료 간 `.agents/workflows/`(복수, Codelab) vs `.agent/workflows/`(단수, 일부 IDE 문서) 표기가 엇갈림 → **덱 인쇄 전 antigravity.google 공식 docs로 1회 최종 확정**.

### D-4. 공통 조작(`/`·`@`) + 스킬 호출 방식 검증 — 신규 슬라이드(§5-6) 근거
- **`@` 파일·컨텍스트 언급**은 Claude·Codex·Antigravity **공통**.
- **스킬 호출은 셋 다 가능**하되 메커니즘이 다름 (기존 덱이 "Antigravity=workflows만 `/`, 스킬은 자동"으로 과도하게 단정했던 부분 정정):
  - Claude: 스킬=슬래시 커맨드 통합 → `/skill-name`
  - Codex: `/` 커맨드 + 인라인 스킬 `$skill-name`
  - **Antigravity: 스킬=의미 기반 자동 호출(이름 지목 시 강제), workflows=`/workflow-name`. 스킬의 슬래시 노출은 확산 중이나 아직 부분적**(글로벌 스킬이 슬래시로 안 뜨는 사례 보고).
- 결론: "스킬은 `/`, 파일은 `@`"는 **슬라이드 표면 메시지로 유지 가능**, 도구별 결 차이는 발표자 노트로.

### D-3. 덱 반영 — 슬라이드별 조치
| 슬라이드 | 조치 |
|----------|------|
| 1 (대상 목록) | "Gemini · Google Antigravity" → **"Antigravity" 단일** (Gemini CLI 개인용 종료 각주) |
| 6 (도구별 위치) | "Gemini/Antigravity" 열 → **Antigravity 단일**, `GEMINI.md` → `.agents/agents.md`, `/Permission`·PowerShell 경고 삭제(Gemini CLI 잔재) |
| 8 (Skills 도구별) | Gemini CLI 섹션 삭제 → Antigravity로 흡수, `.gemini/commands/*.toml` 제거 |
| 9 (Commands 예시) | "Gemini Commands TOML 예시" → **Antigravity Workflow 예시**(`.agents/workflows/*.md`)로 교체 |
| 12 (Subagent) | Gemini 열 → Antigravity로 흡수. Antigravity **멀티에이전트(Agent Manager) 오케스트레이션** 반영 |
| 13 (총정리 표) | **4열 → 3열** (Claude Code / Codex / Antigravity), Antigravity 행 전부 `.agents/*` 최신 경로로 |

---

## C. 출처
- Claude Code Skills / commands 통합: https://code.claude.com/docs/en/skills
- Claude Code Plugins 출시(2025-10-09): https://code.claude.com/docs/en/discover-plugins , https://support.claude.com/en/articles/12138966-release-notes
- Codex Agent Skills 경로: https://developers.openai.com/codex/skills
- SKILL.md 오픈 표준(교차 도구): https://www.agensi.io/learn/agent-skills-open-standard
- Antigravity Skills 경로(IDE `.agents/skills/`, CLI `.agent/skills/`): https://codelabs.developers.google.com/getting-started-with-antigravity-skills
- Gemini CLI 커스텀 커맨드 TOML(`prompt`·`description`): https://geminicli.com/docs/cli/custom-commands/
- **Gemini CLI → Antigravity CLI 전환(2026-06-18 종료)**: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/ , https://github.com/google-gemini/gemini-cli/discussions/27274
- **Antigravity 최신 구조(`.agents/agents.md`·`.agents/skills/`·`.agents/workflows/`)**: https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity
- **공통 조작 `/`·`@`·Codex `$skill-name`**: https://developers.openai.com/codex/cli/slash-commands , https://developers.openai.com/codex/skills , https://antigravity.google/docs/rules-workflows
- **Skills 오픈 표준 수렴 타임라인(2025-12 Anthropic 공개 → 48h MS·OpenAI → 2026-01 Antigravity → 2026-03 32개 도구)**: https://www.mindstudio.ai/blog/agent-skills-open-standard-claude-openai-google , https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- **Antigravity Rules/Workflows/Skills 역할 구분(workflows 폐기 아님, skill=1작업·workflow=여러 skill 파이프라인)**: https://antigravity.google/docs/rules-workflows , https://www.kdnuggets.com/build-better-ai-agents-with-google-antigravity-skills-and-workflows
