# 실행 흐름

## 라우팅 표

| 상황 | 읽을 섹션 |
|---|---|
| 모든 호출 | 사전 점검 |
| 최초 설정 | 최초 사용 + Plan + Apply |
| 최초 이후 정책 변경 | 최초 이후 사용 + Plan + Apply |
| 제거 | 제거 |
| 관리자 교체 | 관리자 교체 |

## 사전 점검

1. 대상 프로젝트 루트와 Git 경계를 절대경로로 확정한다.
2. `git status --short --branch`, remote URL, upstream 유무와 앞섬·뒤처짐을 읽는다.
3. 원격 조회가 필요하면 토큰 값이 아닌 인증 수단의 존재만 확인한다.
4. 현재 서비스의 로그인 계정과 저장소 관리자 권한은 공식 API·CLI 응답으로 확인한다.
5. 정책이 있으면 쓰기 전에 `verify`를 실행한다.
6. 기존 CODEOWNERS, `core.hooksPath`, 두 host 설정을 byte 단위 스냅샷 대상으로 잡는다.
7. 루트 라우팅 정본에 등록된 repository를 모두 확인하고 `discover-participants`로
   서비스의 실제 접근 명단을 조회한다. 활동 이력으로 참여자를 추측하지 않는다.

작업 폴더가 더럽거나 upstream보다 뒤처졌거나 이력이 갈라지면 적용하지 않는다. 읽기
전용 검증은 계속할 수 있다.

## 최초 사용

1. 서명된 기존 정책과 신뢰 파일이 정말 없는지 확인한다. 일부 파일만 없거나 Git 이력에
   기존 정책이 남아 있으면 최초 설정으로 간주하지 않는다.
2. 원격 저장소가 있으면 최초 호출자의 저장소 관리자·소유자 권한을 확인한다. 로컬
   `git init` 상태면 첫 호출자를 임시 관리자로 보되 원격 확인 상태를 `pending`으로 둔다.
3. 최초 호출자의 현재 Git 계정을 subject로 만들고 명시적 `admin` 역할을 배정한다.
   관리자 키의 Codex·Claude 저장 위치와
   공개키 지문을 Plan에 표시한다.
4. 모든 repository의 접근 명단을 합쳐 관리자에게 보여준다. `pm-pl`과 앱별
   `app-doc-lead`를 직접 고르고, `developer`는 포함 또는 제외 목록으로 일괄 고른다.
5. 같은 사람이 관리자와 앱 문서 작성자를 겸하면 `admin`과 `pm-pl` 또는
   `app-doc-lead`를 각각 배정한다. 역할 상속은 두지 않는다.
6. 앱별 문서 책임자는 담당 앱 목록까지 묶는다. 지정·해제 권한은 최초 관리자에게 둔다.
7. 세 provider CODEOWNERS, 서명 정책, 로컬 Git 훅, AI instruction·host 훅을 각각
   별도 승인 항목으로 보여준 뒤 Apply한다.

## 최초 이후 사용

1. 현재 정책 서명, 생성 목록, 관리 블록과 Codex·Claude 관리자 키 지문을 먼저 검증한다.
2. 검증된 `admin`만 관리자·PM/PL·developer 계정, 앱별 문서 책임자, 담당 앱과 경로 정책 변경을
   Apply할 수 있다. `pm-pl`과 `app-doc-lead`의 요청은 변경안으로만 보고한다.
3. 변경 전후 subject, provider·host 계정, 명시적 역할, 앱 배정과 경로 판정 차이를
   Plan으로 보여준다.
4. `developer`는 관리자가 원할 때 포함·제외 목록으로 일괄 갱신한다. 이 역할의 누락은
   소스 코드 편집이나 `team` 범위를 차단하지 않는다.
5. 변경된 Plan hash에 별도 승인을 받은 뒤 Apply하고 세 계층을 다시 검증한다.

## Plan

사용자와 다음 두 묶음을 확정한다. 한 번에 불명확한 질문은 최대 3개만 한다.

1. 프로젝트 식별자, 애플리케이션, `admin`·전역 `pm-pl`·앱별 `app-doc-lead`와 담당 앱
2. `developer` 포함·제외 기준과 등록 역할별 GitHub·GitLab·Gitea 계정
3. 논리 프로젝트에 매핑된 모든 repository와 프로젝트가 이미 정한 보호 브랜치·승인 규칙

먼저 다음 명령으로 실제 접근 명단을 조회한다. 결과가 일부 repository에서 실패하면
누락 범위를 표시하고 추측으로 역할을 넣지 않는다.

```text
python {skill-root}/scripts/project_write_access.py discover-participants \
  --config {config-json}
```

`team` 경로는 Git 저장소 자체에서 쓰기 권한을 받은 일반 기여자에게 열리고,
관리자·앱 핵심 문서는 서명된 역할과 앱 배정으로 판정한다.

설정 JSON은 `references/policy-schema.md` 형식으로 임시 안전 경로에 만든다. 토큰과
개인키를 넣지 않는다.

```text
python {skill-root}/scripts/project_write_access.py plan \
  --project-root {project-root} \
  --config {config-json}
```

Windows PowerShell에서도 같은 인자를 한 줄 또는 백틱 줄바꿈으로 전달할 수 있다.
출력된 `plan_hash`, 충돌, 원격 미적용 항목을 사용자에게 보여준다.

## Apply

로컬·공유 파일 적용 승인을 받은 뒤에만 실행한다.

```text
python {skill-root}/scripts/project_write_access.py apply \
  --project-root {project-root} \
  --config {config-json} \
  --approve-plan-hash {plan-hash}
```

최초 설정에서 원격 저장소가 있으면 공식 API·CLI로 관리자 권한을 확인한 증거의 요약
해시를 `--provider-admin-evidence`로 전달한다. 이 값은 자격 증명이 아니며 토큰을 넣지
않는다. 백업 관리자 키를 사용할 때만 `--admin-key`를 추가한다.

Apply 뒤에는 즉시 `verify`를 실행한다. 파일 적용이 성공해도 원격 서버 규칙은 별도
승인과 API 적용이 끝나기 전까지 `미적용`이다.

권한이 있는 `pm-pl` 또는 해당 앱의 `app-doc-lead`가 앱 핵심 문서를 편집하려는
경우에도 Apply 승인과 섞지 않는다. `design-doc`·`context-doc`이 자동 선택된 경우를
포함해 실제 편집 직전에 다음 내용을 보여주고 별도 답변을 받는다.

```text
앱 핵심 문서를 만들거나 수정하려고 합니다.
대상 앱: {application}
대상 파일: {exact paths}
문서 종류와 역할: DESIGN.md / *-context.md / *-instruction.md 중 해당 항목 설명
현재 역할과 앱 범위: {roles and application scope}
수정 요약·이유: {summary and reason}
이 변경에 한해 진행할까요?
```

번들의 guard `check-path`가 `decision=confirm`을 반환하면 이 질문이 필요하다는 뜻이다.
활성으로 검증된 AI `PreToolUse` 훅은 실제 쓰기 도구 호출에 `permissionDecision=ask`를
반환해 사용자 확인을 띄운다. 질문 뒤 대상 경로나 변경 내용이 달라지면 이전 답변을
재사용하지 않는다. 표준 `pre-commit`·`pre-push`는 비대화형이므로 이 질문을 대신하지
않는다.

## 제거

1. 현재 정책과 관리자 키를 검증한다.
2. 관리 블록, 생성 파일, 로컬 Git 설정 복구, host 설정 제거의 Plan을 따로 보여준다.
3. 원격 브랜치 규칙 제거는 파일 제거와 다른 승인 항목으로 둔다.
4. 관리 목록 밖 파일이나 사용자 작성 영역이 바뀌어 있으면 자동 제거하지 않는다.
5. 관리자 키는 마지막에 폐기하며 Codex·Claude 두 사본과 사용자가 제시한 백업 범위를
   분리해 보여준다.

```text
python {skill-root}/scripts/project_write_access.py remove-plan \
  --project-root {project-root} \
  --delete-keys

python {skill-root}/scripts/project_write_access.py remove \
  --project-root {project-root} \
  --approve-plan-hash {removal-plan-hash} \
  --delete-keys
```

`--delete-keys`는 Codex·Claude의 프로젝트 관리자 키 사본까지 폐기하기로 별도 승인한
경우에만 사용한다. 원격 브랜치 규칙은 이 명령이 제거하지 않는다.

## 관리자 교체

1. 기존 또는 백업 개인키로 현재 서명과 지문을 검증한다.
2. 새 관리자와 세 서비스 계정을 확인한다.
3. 새 키 생성 위치, 기존 키 폐기 범위, 정책·서명·생성 목록 변경 Plan을 보여준다.
4. 별도 승인 뒤 새 정책을 적용하고 두 host 키 사본의 지문을 다시 대조한다.
5. 원격 규칙이 새 소유자를 실제 유효한 승인자로 인식하는지 확인한 뒤에만 기존 키를
   폐기한다.

기존 키나 일치하는 백업 키가 없으면 교체·초기화하지 않는다.

```text
python {skill-root}/scripts/project_write_access.py rotate-plan \
  --project-root {project-root} \
  --config {new-config-json}

python {skill-root}/scripts/project_write_access.py rotate \
  --project-root {project-root} \
  --config {new-config-json} \
  --approve-plan-hash {rotation-plan-hash}
```

교체 Apply는 기존 키로 현재 정책을 먼저 검증하고 새 Ed25519 키·신뢰 정보·정책
서명을 하나의 로컬 트랜잭션으로 바꾼다. 실패하면 기존 두 키 사본과 정책 파일을
복구한다.
