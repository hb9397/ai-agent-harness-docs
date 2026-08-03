# 증거 기반 커밋 메시지 예시

저장소 지침과 최근 log가 요구하는 언어·scope·길이를 우선한다. 복합 변경의 body는 핵심
의도를 먼저 설명하고 실제 추가·수정·제거 사항과 이유를 bullet로 구체화한다. 검증 결과는
해당 명령을 실제로 실행해 성공한 경우에만 적는다.

## 좋은 예시

```text
feat(auth): 조직 계정 OAuth 로그인 지원

조직 사용자가 기존 계정을 유지한 채 승인된 OAuth 공급자로 로그인할 수 있게 한다.

- 공급자별 token exchange adapter를 추가해 인증 책임과 API 차이를 분리
- 기존 이메일 로그인 경로를 유지해 점진적 전환과 rollback을 지원
- callback state 검증을 공통화해 공급자별 누락 가능성을 제거

검증: `npm test -- auth` 통과 (42 tests)
```

```text
fix(order): 취소 트랜잭션의 재고 복구 누락 수정

취소된 수량이 가용 재고로 돌아오지 않아 후속 주문이 막히는 회귀를 해결한다.

- 주문 상태 전환과 재고 복구를 같은 트랜잭션으로 이동해 부분 성공을 방지
- 주문 잠금 안에서 복구하도록 수정해 동시 취소의 중복 반영을 차단
- 실패 재현과 동시 취소 사례를 추가해 수정 전후 동작을 고정

검증: `./mvnw test -Dtest=OrderCancelTest` 통과
```

```text
refactor(domain): 회원 생성 경로를 정적 팩토리로 통합

필수값과 선택값이 섞인 생성자 호출의 오류 가능성을 줄이고 도메인 불변식을 한곳에서
검증한다.

- 외부 생성자를 정적 팩토리로 대체해 필수값 검증을 단일화
- builder는 persistence 조립 경로에만 남겨 임의 상태 생성을 제한
- 호출부를 새 생성 계약으로 옮기고 사용되지 않는 생성자를 제거

검증: `./gradlew test --tests '*MemberTest'` 통과
```

```text
docs(governance): 지원 근거와 제한 사항 명확화

운영 문서의 주장을 현재 검증 증거와 일치시켜 릴리스 판단의 오해를 줄인다.

- 지원 기능별 근거와 관찰 시점을 추가해 추적 가능성을 확보
- 실제 동작과 다른 버전 설명을 현재 manifest 기준으로 수정
- 검증되지 않은 런타임 동등성 문구를 제거해 보장 범위를 과장하지 않음

검증: 문서 링크 검사와 `git diff --check` 통과
```

## 피해야 할 예시

```text
# body와 결정 근거가 없음
feat(auth): 소셜 로그인 추가

# 실행하지 않은 검증을 성공으로 주장
fix(order): 재고 복구 오류 수정

모든 테스트가 통과했다.

# 서로 다른 관심사를 한 커밋으로 숨김
feat(auth): 로그인 추가 및 주문 취소 수정

# 요청이나 저장소 정책 없이 attribution trailer 삽입
Co-Authored-By: AI Agent <agent@example.invalid>
```

## scope 결정 방법

적용되는 `AGENTS.md`, 최근 log, staged diff 순으로 근거를 확인한다. scope가 선택 사항인
저장소에서는 억지로 만들지 말고, 복수 앱 저장소에서는 앱과 모듈 경계를 함께 표현한다.

| 변경 파일 경로 예시 | 가능한 scope |
|---|---|
| `src/auth/login.ts` | `auth` |
| `components/Button.jsx` | `ui` |
| `api/users/route.ts` | `api` |
| `scripts/deploy.sh` | `ci` |
| `package.json`, `requirements.txt` | `deps` |
| `README.md`, `docs/` | `docs` |

`CLAUDE.md`가 `AGENTS.md`를 가리키는 bridge라면 중복 규칙으로 해석하지 않는다. 서로
충돌하는 규칙이나 불명확한 scope가 있으면 커밋 전에 사용자에게 확인한다.
