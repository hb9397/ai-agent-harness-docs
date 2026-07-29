#!/bin/bash
# 프로젝트 룰 검사 스크립트 (범용 — 언어 무관)
# 사용: bash scan.sh [대상 디렉토리]
# 동작: git repo 내에서 실행 시 변경된 코드 파일만 검사 (성능/노이즈 최소화)
#       git repo 밖에서 실행 시 $TARGET 전체 스캔

TARGET="${1:-.}"

# 코드 파일 확장자 패턴
CODE_EXT_PATTERN="\.(java|kt|ts|tsx|js|jsx|py|go|rs)$"

scan_code() {
  grep -rn \
    --include="*.java" --include="*.kt" \
    --include="*.ts" --include="*.tsx" \
    --include="*.js" --include="*.jsx" \
    --include="*.py" --include="*.go" --include="*.rs" \
    "$@"
}

echo "=== 프로젝트 룰 검사 스캔 ==="

# ── 스캔 대상 결정 ──────────────────────────────────────────────────
# git repo: 변경된 코드 파일만 | 비-git: $TARGET 전체
SCAN_TARGETS=()

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "## 변경 파일 목록"

  CHANGED=$(
    { git diff --name-only HEAD 2>/dev/null; git diff --name-only --staged 2>/dev/null; } \
    | sort -u
  )

  if [ -z "$CHANGED" ]; then
    echo "변경된 파일이 없습니다. 검사를 종료합니다."
    exit 0
  fi

  echo "$CHANGED"
  echo ""

  # 존재하는 코드 파일만 스캔 대상으로 추가 (확장자 필터)
  while IFS= read -r f; do
    if [[ -f "$f" && "$f" =~ $CODE_EXT_PATTERN ]]; then
      SCAN_TARGETS+=("$f")
    fi
  done <<< "$CHANGED"

  if [ ${#SCAN_TARGETS[@]} -eq 0 ]; then
    echo "변경된 코드 파일이 없습니다 (md/yml/json 등 비코드 파일만 변경됨). 검사를 종료합니다."
    exit 0
  fi

  echo "대상 코드 파일 (${#SCAN_TARGETS[@]}개):"
  printf '  %s\n' "${SCAN_TARGETS[@]}"
  echo ""
else
  # git 환경 아님 — 전체 디렉토리 스캔
  SCAN_TARGETS=("$TARGET")
  echo "대상: $TARGET (전체 스캔)"
  echo ""
fi
# ────────────────────────────────────────────────────────────────────

# --- 1. 에러 처리 ---
echo "## 1. 에러 처리"
echo ""

echo "### 빈 catch/except 블록"
scan_code "catch.*{}" "${SCAN_TARGETS[@]}" 2>/dev/null
grep -n "except.*:[[:space:]]*$" "${SCAN_TARGETS[@]}" 2>/dev/null
scan_code "catch\s*{" "${SCAN_TARGETS[@]}" 2>/dev/null | head -20
echo "(위 결과 중 빈 블록 확인 필요)"
echo ""

echo "### 에러 무시 주석 (// ignore, # noqa 등)"
scan_code -i "// *ignore\|# *ignore\|# *noqa" "${SCAN_TARGETS[@]}" 2>/dev/null || echo "(없음)"
echo ""

# --- 2. 타임아웃 ---
echo "## 2. 외부 호출 (타임아웃 확인 필요)"
echo ""
scan_code "fetch(\|axios\.\|requests\.\|HttpClient\|http\.Get\|http\.Post" "${SCAN_TARGETS[@]}" 2>/dev/null | head -20 || echo "(없음)"
echo ""

# --- 3. 민감 정보 ---
echo "## 3. 민감 정보"
echo ""

echo "### 하드코딩된 비밀번호/키/토큰"
scan_code -iE "(password|apikey|api_key|secret|token)\s*[:=]\s*[\"']" "${SCAN_TARGETS[@]}" 2>/dev/null \
  | grep -iv "test\|mock\|example\|placeholder\|TODO\|env\." | head -20 || echo "(없음)"
echo ""

echo "### .env / 설정 파일 변경"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --name-only --staged 2>/dev/null \
    | grep -iE "\.env|credential|secret|application\.yml|application\.properties" || echo "(없음)"
fi
echo ""

# --- 4. TODO ---
echo "## 4. TODO 주석"
echo ""

echo "### 모든 TODO/FIXME/HACK"
scan_code "TODO\|FIXME\|HACK\|XXX" "${SCAN_TARGETS[@]}" 2>/dev/null | head -20 || echo "(없음)"
echo ""

echo "### 기한 없는 TODO"
scan_code "TODO" "${SCAN_TARGETS[@]}" 2>/dev/null \
  | grep -v "TODO(@\|TODO(\|#[0-9]" | head -20 || echo "(없음)"
echo ""

# --- 5. 테스트 ---
echo "## 5. 테스트 존재 여부"
echo ""

echo "### 변경된 비즈니스 로직 파일"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --name-only HEAD 2>/dev/null \
    | grep -ivE "test|spec|mock|fixture|\.env|\.md|\.json|\.yml|\.yaml" | head -20 || echo "(없음)"
fi
echo ""

echo "### 테스트 파일 목록"
find "$TARGET" \( -name "*Test.*" -o -name "*Spec.*" -o -name "*.test.*" -o -name "*.spec.*" -o -name "test_*" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -20 || echo "(없음)"
echo ""

echo "=== 스캔 완료 ==="
