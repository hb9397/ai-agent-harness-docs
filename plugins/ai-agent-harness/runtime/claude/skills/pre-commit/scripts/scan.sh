#!/bin/bash
# 프로젝트 룰 검사 스크립트 (범용 — 언어 무관)
# 사용: bash /absolute/path/to/this-skill/scripts/scan.sh [대상 디렉토리]
# 동작: 대상이 git repo 안이면 그 대상 경계의 tracked/untracked 변경만 검사한다.
#       git repo 밖이면 대상 디렉토리를 재귀 검사한다.

TARGET_INPUT="${1:-.}"
CODE_EXT_PATTERN='\.(java|kt|ts|tsx|js|jsx|py|go|rs)$'
IS_GIT=false
SCAN_TARGETS=()
CHANGED_FILES=()

if [[ ! -d "$TARGET_INPUT" ]]; then
  printf '오류: 검사 대상 디렉토리가 없거나 디렉토리가 아닙니다: %s\n' "$TARGET_INPUT" >&2
  exit 2
fi

TARGET_ABS="$(cd -- "$TARGET_INPUT" 2>/dev/null && pwd -P)"
if [[ -z "$TARGET_ABS" ]]; then
  printf '오류: 검사 대상 경로를 해석할 수 없습니다: %s\n' "$TARGET_INPUT" >&2
  exit 2
fi

append_changed() {
  local candidate="$1"
  local existing
  for existing in "${CHANGED_FILES[@]}"; do
    [[ "$existing" == "$candidate" ]] && return
  done
  CHANGED_FILES+=("$candidate")
}

scan_code() {
  local grep_args=()
  while [[ $# -gt 0 && "$1" == -* ]]; do
    grep_args+=("$1")
    shift
  done
  local pattern="$1"
  shift
  grep -rnH "${grep_args[@]}" \
    --include="*.java" --include="*.kt" \
    --include="*.ts" --include="*.tsx" \
    --include="*.js" --include="*.jsx" \
    --include="*.py" --include="*.go" --include="*.rs" \
    -- "$pattern" "$@"
}

echo "=== 프로젝트 룰 검사 스캔 ==="

# ── 스캔 대상 결정 ──────────────────────────────────────────────────
if git -C "$TARGET_ABS" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  IS_GIT=true
  REPO_ROOT="$(git -C "$TARGET_ABS" rev-parse --show-toplevel)"
  TARGET_PREFIX="$(git -C "$TARGET_ABS" rev-parse --show-prefix)"
  PATHSPEC="${TARGET_PREFIX%/}"
  [[ -z "$PATHSPEC" ]] && PATHSPEC="."

  while IFS= read -r -d '' file; do append_changed "$file"; done \
    < <(git -C "$REPO_ROOT" diff --name-only -z --diff-filter=ACMRD -- "$PATHSPEC" 2>/dev/null)
  while IFS= read -r -d '' file; do append_changed "$file"; done \
    < <(git -C "$REPO_ROOT" diff --cached --name-only -z --diff-filter=ACMRD -- "$PATHSPEC" 2>/dev/null)
  while IFS= read -r -d '' file; do append_changed "$file"; done \
    < <(git -C "$REPO_ROOT" ls-files --others --exclude-standard -z -- "$PATHSPEC" 2>/dev/null)

  cd -- "$REPO_ROOT" || exit 2
  FIND_TARGET="$PATHSPEC"
  echo "## 변경 파일 목록"
  if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
    echo "확인된 대상 경계에 변경된 파일이 없습니다. 검사를 종료합니다."
    exit 0
  fi
  printf '%s\n' "${CHANGED_FILES[@]}"
  echo ""

  for file in "${CHANGED_FILES[@]}"; do
    if [[ -f "$file" && "$file" =~ $CODE_EXT_PATTERN ]]; then
      SCAN_TARGETS+=("$file")
    fi
  done

  if [[ ${#SCAN_TARGETS[@]} -eq 0 ]]; then
    echo "변경된 코드 파일이 없습니다 (md/yml/json 등 비코드 파일만 변경됨). 검사를 종료합니다."
    exit 0
  fi

  echo "대상 코드 파일 (${#SCAN_TARGETS[@]}개):"
  printf '  %s\n' "${SCAN_TARGETS[@]}"
  echo ""
else
  FIND_TARGET="$TARGET_ABS"
  SCAN_TARGETS=("$TARGET_ABS")
  echo "대상: $TARGET_ABS (비-git 재귀 전체 스캔)"
  echo ""
fi
# ────────────────────────────────────────────────────────────────────

echo "## 1. 에러 처리"
echo ""
echo "### 빈 catch/except 블록"
scan_code -E 'catch[[:space:]]*\([^)]*\)[[:space:]]*\{[[:space:]]*\}' "${SCAN_TARGETS[@]}" 2>/dev/null
scan_code -E 'except([^:]*)?:[[:space:]]*$' "${SCAN_TARGETS[@]}" 2>/dev/null
scan_code -E 'catch[[:space:]]*(\([^)]*\))?[[:space:]]*\{' "${SCAN_TARGETS[@]}" 2>/dev/null | head -20
echo "(위 결과 중 빈 블록 확인 필요)"
echo ""

echo "### 에러 무시 주석 (// ignore, # noqa 등)"
scan_code -iE '//[[:space:]]*ignore|#[[:space:]]*ignore|#[[:space:]]*noqa' "${SCAN_TARGETS[@]}" 2>/dev/null || echo "(없음)"
echo ""

echo "## 2. 외부 호출 (타임아웃 확인 필요)"
echo ""
scan_code -E 'fetch\(|axios\.|requests\.|HttpClient|http\.Get|http\.Post' "${SCAN_TARGETS[@]}" 2>/dev/null | head -20 || echo "(없음)"
echo ""

echo "## 3. 민감 정보"
echo ""
echo "### 하드코딩된 비밀번호/키/토큰"
scan_code -iE "(password|apikey|api_key|secret|token)[[:space:]]*[:=][[:space:]]*[\"']" "${SCAN_TARGETS[@]}" 2>/dev/null \
  | grep -ivE 'test|mock|example|placeholder|TODO|env\.' | head -20 || echo "(없음)"
echo ""

echo "### .env / 설정 파일 변경"
if [[ "$IS_GIT" == true ]]; then
  sensitive_found=false
  for file in "${CHANGED_FILES[@]}"; do
    if [[ "$file" =~ \.env|credential|secret|application\.yml|application\.properties ]]; then
      printf '%s\n' "$file"
      sensitive_found=true
    fi
  done
  [[ "$sensitive_found" == false ]] && echo "(없음)"
else
  echo "(git 변경 목록 없음)"
fi
echo ""

echo "## 4. TODO 주석"
echo ""
echo "### 모든 TODO/FIXME/HACK"
scan_code -E 'TODO|FIXME|HACK|XXX' "${SCAN_TARGETS[@]}" 2>/dev/null | head -20 || echo "(없음)"
echo ""

echo "### 기한 없는 TODO"
scan_code 'TODO' "${SCAN_TARGETS[@]}" 2>/dev/null \
  | grep -vE 'TODO@|TODO\(|#[0-9]' | head -20 || echo "(없음)"
echo ""

echo "## 5. 테스트 존재 여부"
echo ""
echo "### 변경된 비즈니스 로직 파일"
if [[ "$IS_GIT" == true ]]; then
  business_found=false
  for file in "${CHANGED_FILES[@]}"; do
    if [[ ! "$file" =~ test|spec|mock|fixture|\.env|\.md$|\.json$|\.ya?ml$ ]]; then
      printf '%s\n' "$file"
      business_found=true
    fi
  done
  [[ "$business_found" == false ]] && echo "(없음)"
else
  echo "(git 변경 목록 없음)"
fi
echo ""

echo "### 테스트 파일 목록"
find "$FIND_TARGET" \( -name "*Test.*" -o -name "*Spec.*" -o -name "*.test.*" -o -name "*.spec.*" -o -name "test_*" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -20 || echo "(없음)"
echo ""

echo "=== 스캔 완료 ==="
