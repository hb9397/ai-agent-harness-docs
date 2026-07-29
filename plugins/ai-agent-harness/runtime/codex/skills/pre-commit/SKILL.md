---
name: pre-commit
description: >
  커밋 전 코드 검사가 필요할 때 이 스킬을 사용한다.
  '커밋 전 검사', '규칙 위반 확인', '코드 점검', 'pre-commit',
  '올려도 되는지 확인해줘' 요청이 오면 이 스킬로 처리한다.
  변경 파일 대상으로 에러 처리·민감 정보·TODO 형식 등 규칙 위반을 자동 검사.
allowed-tools: Read, Glob, Grep, Bash
disable-model-invocation: true
---

# 프로젝트 룰 검사

이 스킬이 호출되면 변경된 파일을 대상으로 아래 검사를 즉시 실행하고, [template.md](template.md) 형식으로 결과를 보고하세요.

---

## STEP 0 — 프로젝트 유형 확인 (C-1 확인 단계)

검사 범위를 확정하기 위해 **반드시** 아래를 수행한다.

1. 현재 수행 위치에서 프로젝트 구조를 탐색한다 (git repo 경계, 하위 앱 폴더 후보 스캔).
2. **단일 애플리케이션 프로젝트**인지 **복수 애플리케이션 프로젝트**인지 판정한다.
3. 판정 결과 + 검사 대상 애플리케이션(폴더)을 사용자에게 **반드시 재확인**한다.
4. 확인된 범위 밖은 건드리지 않는다.

---

## 실행 방법

1. `git diff --name-only`로 변경된 파일 목록 수집 (staged + unstaged)
2. `bash scripts/scan.sh`로 패턴 일괄 검색
3. 스캔 결과 + 수동 분석으로 위반 사항 판정
4. template.md 형식으로 결과 보고

## 검사 항목

검사 항목 상세 정의는 `prompts/check-rules.md` 참조.
`scripts/scan.sh`은 이 규칙의 자동 탐지 구현이다.
