# 변경 파일 감지 규칙 (change-detection)

## 라우팅 표

| 조건 | 읽을 섹션 |
| ---- | --------- |
| git 적용 여부 확인 | [Git 감지] |
| 특정 파일 지정 + git 있음 | [Git Diff — 특정 파일] |
| 특정 파일 지정 + git 없음 | [Mtime — 특정 파일] |
| 파일 미지정 + git 있음 | [Git Diff — 전체 변경 파일] |
| 파일 미지정 + git 없음 | [사용자 질문] |

---

## [Git 감지]

```bash
git rev-parse --is-inside-work-tree 2>/dev/null
```

- 출력이 `true`이면 → git 적용됨
- 명령어 실패(exit code != 0) 또는 출력 없음이면 → git 미적용

---

## [Git Diff — 특정 파일]

지정된 파일에 대해 아래 명령어를 실행한다.

```bash
# unstaged + staged 변경사항 확인
git diff HEAD -- <파일경로> 2>/dev/null | head -100

# 위 명령어 결과가 비어 있으면 마지막 커밋 기준으로 비교
git diff HEAD~1 HEAD -- <파일경로> 2>/dev/null | head -100
```

추출된 diff를 Step 4 주석 작성의 맥락(변경된 코드 내용)으로 활용한다.
diff가 추출되면 [변경 범위 추출] 섹션을 추가로 수행하여 변경된 블록 목록을 확정한다.

---

## [변경 범위 추출]

diff 결과에서 **실제로 변경된 함수·클래스·블록**의 목록을 추출한다.

```bash
# hunk 헤더(@@ ... @@)에서 함수명 추출
git diff HEAD -- <파일경로> 2>/dev/null | grep "^@@"

# 변경된 라인 번호 범위만 추출 (추가·삭제 행 기준)
git diff HEAD -- <파일경로> 2>/dev/null \
  | grep -E "^\+\+\+ |^@@ " | head -50
```

추출 결과로 **변경 블록 목록**을 작성한다:

```text
변경된 블록:
- 라인 범위: <start>~<end>  → 해당 범위를 감싸는 함수/클래스명: <name>
- 라인 범위: <start>~<end>  → 해당 범위를 감싸는 함수/클래스명: <name>
```

이 목록을 Step 4 주석 작성 시 **변경 범위 한정 판단**의 기준으로 전달한다.
목록에 없는 함수·클래스·변수는 기존 주석을 그대로 유지한다.

---

## [Git Diff — 전체 변경 파일]

```bash
# unstaged 변경 파일 + staged 변경 파일 목록
git diff --name-only HEAD 2>/dev/null
git diff --name-only --cached 2>/dev/null
```

- 두 명령어의 결과를 합산해 중복을 제거한 파일 목록을 대상으로 한다.
- 변경된 파일이 없으면 사용자에게 알리고 종료한다.

  > "변경된 파일이 감지되지 않았습니다. 직접 파일을 지정해 주세요."

---

## [Mtime — 특정 파일]

지정된 파일의 마지막 수정 시점을 확인한다.

```bash
# Linux / macOS
stat -c "%y %n" <파일경로> 2>/dev/null \
  || stat -f "%Sm %N" -t "%Y-%m-%d %H:%M:%S" <파일경로> 2>/dev/null

# Windows (PowerShell 경유)
powershell -Command "(Get-Item '<파일경로>').LastWriteTime" 2>/dev/null
```

확인된 수정 시점을 Step 4 주석 작성의 맥락(변경 이력 날짜)으로 활용한다.

---

## [사용자 질문]

git이 적용되지 않았고 특정 파일이 지정되지 않은 경우:

> "주석을 적용할 파일 또는 디렉토리 경로를 지정해 주세요."

사용자가 경로를 제공하면 [Mtime — 특정 파일] 섹션을 참조하여 진행한다.
