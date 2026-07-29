# Task B — 패턴·아키텍처 분석 (pattern-audit)

**역할**: 최근 코드 변경에서 새로운 패턴, 아키텍처, 예외처리 방식이 문서에 반영됐는지 확인하는 전담 에이전트.

---

## 1. 최근 변경 이력 파악

```bash
git log --oneline -30
git diff HEAD~5..HEAD --stat
```

`--stat` 결과에서 핵심 변경 파일을 선별하여 해당 파일만 `cat` / `view` 로 내용을 확인한다.
변경량이 많은 파일, 새로 추가된 파일, 설정 파일 위주로 우선 확인한다.

## 2. 코드 패턴 분석

```bash
# 예외처리 패턴
grep -rn "except\|try:\|catch\|onError" src --include="*.py" --include="*.js" \
  --include="*.jsx" --include="*.ts" --include="*.tsx" 2>/dev/null | head -40

# 미들웨어 / 데코레이터 / 훅
grep -rn "@app\|@router\|middleware\|use[A-Z]" src \
  --include="*.py" --include="*.js" --include="*.jsx" 2>/dev/null | head -30

# 설정 파일
find . -maxdepth 3 -name "settings*.py" -o -name "config*.py" -o -name "*.config.js" \
  ! -path "*/node_modules/*" ! -path "*/venv/*" 2>/dev/null | xargs cat 2>/dev/null | head -80
```

## 3. 문서와 비교

| 확인 항목 | 방법 |
|-----------|------|
| 새 패턴 누락 | 코드에서 반복되는 새 패턴이 문서에 없는가 |
| 아키텍처 변경 | 디렉토리 구조·레이어가 바뀌었는데 문서가 구식인가 |
| 예외처리 가이드 | 공통 예외 패턴이 문서에 기술됐는가 |
| 환경변수 | 새 환경변수가 추가됐는데 문서에 안내 없는가 |
