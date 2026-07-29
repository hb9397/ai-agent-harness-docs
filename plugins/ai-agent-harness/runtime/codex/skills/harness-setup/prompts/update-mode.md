# prompts/update-mode.md
# 역할: 이미 세팅된 프로젝트에서 .docs·루트 컨텍스트를 갱신하는 절차

---

## 전제

- SKILL.md Step 3에서 **갱신 모드**로 판정.
- `.docs/` 또는 `AGENTS.md`가 존재.
- 프로젝트 유형(단일/복수)은 Step 2에서 확정.

---

## 1. 플러그인 설치 상태 확인

후속 스킬 사용이 실패하면 `ai-agent-harness` 플러그인 설치 상태와 새 세션 여부를 안내한다.
이 스킬은 프로젝트 `.claude/skills/` 또는 `.agents/skills/`를 생성·수정·삭제하지 않는다.

---

## 2. 갱신 계획 사용자 확인

비교 결과를 요약하여 사용자에게 확인받는다:

> ✋ **갱신 대상 확인**
>
> | 유형 | 대상 |
> |------|------|
> | `.docs` 안내·정책 | README/.gitignore/_inbox |
> | 루트 컨텍스트 | AGENTS.md 정본, CLAUDE.md bridge |
> | legacy local skill copy | 읽기 전용 report만 출력 |
>
> 진행하시겠습니까? **(승인 / 수정 / 취소)**

---

## 3. `.docs/` 안내·정책 파일 갱신

`.docs/`가 존재하면(단일·복수 공통) 아래 안내·정책 파일을 최신 템플릿으로 맞춘다.
README/.gitignore는 harness-setup이 단독 관리하므로 **덮어써도 안전**하고, `_inbox/` 내용은 **절대 건드리지 않는다**.

| 파일 | 단일 앱 템플릿 | 복수 앱 템플릿 | 처리 |
|------|----------------|----------------|------|
| `.docs/README.md` | `docs-readme-single.template` | `docs-readme-multi.template` | 덮어쓰기 |
| `.docs/.gitignore` | `docs-gitignore.template` | (동일) | 덮어쓰기 |
| `.docs/_inbox/` | — | — | 없으면 생성(`.gitkeep`+README), 내용 보존 |

```bash
# 프로젝트 유형(Step 2)에 따라 README 템플릿 선택
README_TPL="docs-readme-single.template"   # 복수 앱이면 docs-readme-multi.template

cp "[plugin:harness-setup]/templates/$README_TPL" .docs/README.md
cp "[plugin:harness-setup]/templates/docs-gitignore.template" .docs/.gitignore

# _inbox는 없을 때만 생성 (기존 로컬 파일 보존)
if [ ! -d .docs/_inbox ]; then
  mkdir -p .docs/_inbox
  : > .docs/_inbox/.gitkeep
  cp "[plugin:harness-setup]/templates/inbox-readme.template" .docs/_inbox/README.md
fi
```

> `.docs/`가 아직 없으면 이 단계는 건너뛴다 (다른 경로로 세팅이 진행 중일 수 있음).

---

## 4. 루트 컨텍스트 갱신

`AGENTS.md`가 공통 정본이다. `CLAUDE.md`는 `@AGENTS.md` bridge와 Claude 전용 차이만 둔다.

단일 앱:
- `AGENTS.md`는 `context-doc` 결과를 기준으로 한다.
- `CLAUDE.md`가 bridge가 아니면 `templates/claude-bridge.template` 기준으로 갱신 후보를 제시한다.

복수 앱:
- `.docs/root-context/AGENTS.md`를 루트 `AGENTS.md`로 반영한다.
- `.docs/root-context/CLAUDE.md`가 bridge가 아니면 bridge 템플릿으로 갱신 후보를 제시한다.

---

## 5. 복수 애플리케이션 추가 갱신

프로젝트가 **복수 애플리케이션**인 경우에만 수행.

### 5-1. 루트 컨텍스트 갱신

`.docs/root-context/AGENTS.md`, `.docs/root-context/CLAUDE.md`를 다시 읽어와 루트에 반영한다.

```bash
# .docs/root-context/가 원본. 루트 파일을 갱신.
cp .docs/root-context/AGENTS.md ./AGENTS.md
cp .docs/root-context/CLAUDE.md ./CLAUDE.md
```

> 만약 `.docs/root-context/` 파일이 존재하지 않으면 (다른 스킬에 의해 아직 안 만들어졌거나 삭제된 경우),
> 갱신하지 않고 사용자에게 알린다.

### 5-2. 신규 애플리케이션 감지

Step 2 감지 결과에서 `.docs/{앱}-context.md`가 없는 새 앱 폴더가 발견되면:

```bash
touch ".docs/${new_app}-context.md"
mkdir -p ".docs/${new_app}/context-base"
mkdir -p ".docs/${new_app}/instruction"
mkdir -p ".docs/${new_app}/impl-doc"
```

사용자에게 신규 앱 추가 사실을 알린다.

---

## 6. legacy local skill copy 읽기 전용 report

`.agents/skills/` 또는 `.claude/skills/`가 있으면 다음 기준으로 읽기 전용 분류만 보고한다.

| 분류 | 기준 | 기본 처리 |
|------|------|----------|
| 알려진 옛 하네스 copy | 과거 release inventory와 파일 목록·hash 일치 | 보존, 승인형 migration 후보 |
| 사용자가 수정한 copy | 이름은 같지만 hash 불일치 | 보존, 수동 검토 필요 |
| 무관한 custom skill | 과거 하네스 목록에 없음 | 보존 |
| plugin 이름 충돌 | 현재 plugin 제공 스킬과 같은 이름 | 보존, 충돌 보고 |

승인 전에는 backup·remove·rename을 수행하지 않는다.

---

## 7. 결과 정리

갱신 결과를 요약한다:

```
## 갱신 결과

- `.docs/` 안내·정책: README/.gitignore 갱신됨 / `_inbox/` 유지(또는 신규 생성)
- 루트 컨텍스트: AGENTS 갱신됨 / CLAUDE bridge 갱신됨 / 변경 없음
- (복수앱) 신규 앱 감지: {앱명} (구조 추가됨)
- legacy local skill copy: 읽기 전용 report N건 / 없음
```
