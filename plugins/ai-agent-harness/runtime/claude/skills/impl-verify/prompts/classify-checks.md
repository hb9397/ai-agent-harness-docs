# 자동/수동 분류 규칙 (classify-checks)

추출한 검증 항목을 auto / manual / hybrid 로 분류한다.

---

## auto (자동 실행 가능)

다음 키워드/패턴이 본문에 있으면 auto 후보:

- 명령 실행: `npm`, `pytest`, `yarn`, `python`, `go test`, `cargo`, `mvn`, `gradle`
- HTTP 검증: `curl`, `GET /`, `POST /`, `status 2xx/4xx/5xx`
- 종료 코드: `종료 코드`, `exit code`, `$?`, `0이 아닌`
- 빌드/타입: `build`, `tsc`, `lint`, `mypy`, `typecheck`
- 파일 검증: `파일 존재`, `생성됨`, `삭제됨`, `해시 일치`
- DB 검증: `SELECT`, `레코드 존재`, `row count`
- 마이그레이션: `alembic upgrade`, `prisma migrate`, `migrate up/down`

판정 기준이 **명시적 조건**이어야 한다:
- ✅ "200 응답 + body.id 존재"
- ✅ "pytest 15 passed, 0 failed"
- ❌ "정상 동작"
- ❌ "잘 됨"

명시적 조건이 없으면 manual로 강등.

---

## manual (사람 확인 필요)

다음 패턴은 manual:

- 화면 관련: `렌더링`, `노출`, `표시`, `레이아웃`, `반응형`, `스크롤`, `애니메이션`
- 인터랙션: `클릭`, `입력`, `드래그`, `키보드 탐색`, `포커스`
- UX: `토스트`, `모달`, `안내 메시지`, `사용자 흐름`
- 접근성: `스크린리더`, `aria`, `색 대비`, `Tab 순서`
- 시각적 판단: `깨지지 않는다`, `자연스럽다`, `직관적`

---

## hybrid (자동 + 수동 혼합)

다음 패턴은 hybrid:

- 환경 준비는 자동, 결과 확인은 수동
  - "서버 기동 후 브라우저에서 X 확인" → 서버 기동 auto, 브라우저 manual
- 자동 산출물을 사람이 판정
  - "스냅샷 생성 후 시각 검토" → 스냅샷 auto, 검토 manual
- 자동 실행 + 시각적 확인 필요
  - "스토리북 빌드 후 4상태 렌더링 확인" → 빌드 auto, 렌더링 manual

hybrid 항목은 auto 단계 통과 후 manual 단계로 자동 전환.

---

## 분류 후 보강 정보

각 항목에 추가 메타 부여:

### auto 보강
- `commands`: 실행할 명령 시퀀스 (가능한 한 1줄씩)
- `expected_exit`: 기대 종료 코드
- `expected_stdout_pattern`: 기대 출력 패턴 (정규식 또는 substring)
- `pre_conditions`: 실행 전 필요한 환경 (서버 기동, 마이그레이션 적용 등)

### manual 보강
- `checklist`: 사용자에게 보여줄 체크리스트 항목들
- `context`: 화면 진입 경로, 테스트 데이터 등
- `expected_observations`: 사용자가 확인해야 할 구체 사항

### hybrid 보강
- auto 부분 + manual 부분을 모두 채움
- `handoff_message`: auto → manual 전환 시 사용자에게 안내할 메시지

---

## 분류 신뢰도

분류 신뢰도가 낮으면 manual로 강등:

- 본문이 모호함 (예: "정상 동작 확인")
- 자동 검증 도구가 코드베이스에 없음 (pytest 없는데 "pytest 통과")
- 환경 정보 부족 (어느 URL/포트인지 모름)

신뢰도 낮은 항목은 리포트에 "자동화 불가 — 사용자 확인" 사유 명시.

---

## 분류 예시

| 검증 기준 본문 | 분류 | 근거 |
|---------------|------|------|
| "curl POST /api/sites → 201 + body.id 존재" | auto | curl + 명시적 조건 |
| "pytest tests/sites/ → 전체 통과" | auto | 테스트 명령 + 조건 |
| "로딩 인디케이터 노출" | manual | 시각 판단 |
| "Tab 순서 자연스러움" | manual | 시각 판단 |
| "서버 기동 후 /health 200" | auto | curl 가능 + 조건 |
| "스토리북 4상태 렌더링" | hybrid | 빌드 auto + 시각 manual |
| "정상 동작 확인" | manual | 모호함 |
| "SELECT FROM sites → 1 row" | auto | DB 조회 + 조건 |
