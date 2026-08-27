# 실행 흐름

## 라우팅 표

| 상황 | 읽을 섹션 |
|---|---|
| 모든 호출 | 사전 점검 |
| 최초 설정·정책 변경 | Plan + Apply |
| 제거 | 제거 |
| 관리자 교체 | 관리자 교체 |

## 사전 점검

1. 대상 프로젝트 루트와 Git 경계를 절대경로로 확정한다.
2. `git status --short --branch`, remote URL, upstream 유무와 앞섬·뒤처짐을 읽는다.
3. 원격 조회가 필요하면 토큰 값이 아닌 인증 수단의 존재만 확인한다.
4. 현재 서비스의 로그인 계정과 저장소 관리자 권한은 공식 API·CLI 응답으로 확인한다.
5. 정책이 있으면 쓰기 전에 `verify`를 실행한다.
6. 기존 CODEOWNERS, `core.hooksPath`, 두 host 설정을 byte 단위 스냅샷 대상으로 잡는다.

작업 폴더가 더럽거나 upstream보다 뒤처졌거나 이력이 갈라지면 적용하지 않는다. 읽기
전용 검증은 계속할 수 있다.

## Plan

사용자와 다음 두 묶음을 확정한다. 한 번에 불명확한 질문은 최대 3개만 한다.

1. 프로젝트 식별자, 애플리케이션, 사용자 식별자와 `admin`·`pm-pl`·`developer` 역할
2. 사용자별 GitHub·GitLab·Gitea 계정, 프로젝트가 이미 정한 보호 브랜치와 승인 규칙

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
