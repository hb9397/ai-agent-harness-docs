---
name: humanize-korean
description: "AI·번역투·기계적 문체가 섞인 한국어 문서를 의미·수치·고유명사·인용을 보존하면서 자연스럽게 다듬을 때 사용한다. 문서 산출물 개선은 proposal-only로 수행한다."
allowed-tools: Read, Write, Edit
---

# Humanize Korean

`im-not-ai` v2.3.0을 참고해 하네스 사용자 플러그인 안에 포함한 한국어 문서 윤문 스킬이다. 목적은 “AI 탐지 회피”가 아니라 프로젝트 산출물의 한국어 품질 개선이다.

## 적용 범위

- ChatGPT/Claude/Codex/Gemini가 만든 한국어 초안의 번역투, 반복 표현, 기계적 병렬 구조 완화
- `design-doc`, `context-doc`, `impl-doc`, `impl-fe-be-doc`, `design-prototype-docs`, `harness-bootstrap`, `harness-setup` 산출물의 최종 문장 품질 개선안 제안
- 사용자가 지정한 일부 문단·섹션만 재윤문

## 금지 범위

- 의미, 요구사항, 수치, 날짜, ID, API 경로, 파일 경로, 명령어, 코드, 표 구조, 직접 인용 변경
- 법률·계약·보안·의료·재무 문서의 의무 수준 변경 (`must`, `shall`, `해야 한다`, `금지`, `필수` 등)
- 사용자의 승인 없이 산출물 파일을 직접 덮어쓰기
- Claude 전용 sub-agent나 외부 plugin cache 경로에 의존

## 실행 원칙

1. 먼저 원문 목적과 보호 토큰을 식별한다.
2. 탐지 근거가 있는 span만 다루고, 문체만 다듬되 사실·요구사항·구조는 보존한다.
3. 변경률이 30%를 넘으면 경고하고, 50%를 넘으면 중단한다.
4. 문서 산출물은 기본적으로 “개선안 제안”만 한다. 실제 파일 반영은 사용자 승인 뒤 별도 수행한다.
5. 부분 재윤문 요청이면 지정 범위 밖 문장은 그대로 둔다.
6. `~를 통해`, `~에 의해`, `결론적으로`는 출현만으로 오류가 아니다. 수단·경로·주체·문단 관계를 진단한 뒤 유지·삭제·재작성 후보를 제안하며 기계적으로 치환하지 않는다.

## 보호 토큰

다음은 원문 그대로 유지한다.

- 숫자, 단위, 날짜, 버전, 커밋 SHA, 티켓 ID, 요구사항 ID
- 파일 경로, URL, 명령어, 코드 fence, 인라인 코드
- 표 헤더·열 수·행 수
- 직접 인용문
- 의무 수준 표현: `필수`, `금지`, `해야 한다`, `하지 않는다`, `MUST`, `SHOULD`, `MAY`

## 작업 절차

### STEP 0 — 입력·모드 확인

- 입력이 파일이면 먼저 읽고, 코드 fence·표·경로·식별자를 보호 토큰으로 표시한다.
- 모드는 기본 `standard`다.
  - `fast`: 최소 변경, 명백한 AI/번역투만 완화
  - `standard`: 문장 리듬과 반복 표현까지 다듬음
  - `redo`: 사용자가 지정한 줄 범위만 `standard` 강도로 재윤문하며 범위 밖은 바꾸지 않음
- 산출물 `.md` 후처리라면 `document-refinement` 프로필을 사용한다.

### STEP 1 — 개선안 작성

- 원문 의미를 보존한 윤문안을 작성한다.
- 표, 코드 fence, 경로, ID, 숫자, 날짜는 그대로 둔다.
- 문서 산출물 개선안은 “변경 제안 요약 + 수정안” 형태로 제시한다.
- 문맥 의존 표현은 `span + 진단 근거 + 후보`를 먼저 제시한다. 후보 중 하나를 자동 정답처럼 적용하지 않는다.

### STEP 2 — 자체 검증

- 보호 토큰 누락·변형 여부를 확인한다.
- 변경률을 계산한다.
- 30% 초과면 “과윤문 경고”를 표시한다.
- 50% 초과면 결과를 폐기하고 사용자에게 범위 축소나 강도 조정을 요청한다.

### STEP 3 — 반영 방식

- 일반 텍스트 요청: 윤문본을 답변한다.
- 파일 요청: 기본은 patch proposal 또는 별도 개선안 파일이다.
- `document-refinement`: 사용자 승인 전에는 원본 파일을 쓰지 않는다.
- 승인받은 파일 반영은 `--write-approved`를 명시한 경우에만 수행하며, 검증을 통과한 뒤 같은 디렉터리의 임시 파일을 원자적으로 교체한다.

## 로컬 보조 스크립트

필요하면 현재 로드한 `SKILL.md`의 부모 디렉터리를 `{skill_dir}`로 두고 `{skill_dir}/scripts/humanize_korean.py`를 사용해 deterministic 보호 토큰 검사, 변경률 검사와 문맥 의존 표현 진단을 실행한다. 관리 저장소의 `skills/...` 상대경로를 가정하지 않는다. 스크립트의 `diagnostics`는 검토 후보이며, 해당 span을 자동 치환하지 않는다.

예:

```bash
python "{skill_dir}/scripts/humanize_korean.py" --file .docs/example.md --profile document-refinement
python "{skill_dir}/scripts/humanize_korean.py" --file .docs/example.md --mode redo --redo-range 12:18
```

## 참고 자료

- `references/document-refinement.md`
- `references/taxonomy.md`
- `evals/evals.json`

회귀 검증은 현재 스킬 디렉터리의 `evals/run_evals.py`를 실행한다.
