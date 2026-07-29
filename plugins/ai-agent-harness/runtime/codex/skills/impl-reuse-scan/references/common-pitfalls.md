# 매칭 함정 (common-pitfalls)

false positive(불필요한 재사용 강요)와 false negative(중복 놓침)를 줄이기 위한 가이드.
스캔 결과를 분류하기 전에 이 체크를 한 번 거친다.

---

## false positive 차단 (잘못된 재사용 권고 막기)

다음 케이스는 이름·시그니처가 같아도 **🔴 동일로 분류하지 않는다**.

### 1. 도메인이 다른 동명 자산

```
기존:  domain/billing/User.ts
신규:  domain/marketing/User.ts
```

같은 `User`라도 책임 도메인이 다르면 강제로 묶지 않는다. 🟡 또는 🟢로 강등.
디렉토리 경로(`billing` vs `marketing`)를 도메인 식별자로 사용.

### 2. deprecated / legacy 자산

다음 신호가 있으면 재사용 권고에서 제외:
- 파일 또는 함수 주석에 `@deprecated`, `@legacy`, `DO NOT USE`
- 디렉토리에 `_old`, `legacy`, `deprecated`, `archived`
- 마지막 커밋이 1년 이상 전이고 import 없음

### 3. private/internal 자산

다음은 외부 재사용 대상이 아님:
- 파일/함수 이름이 `_`로 시작 (Python/JS 관례)
- `export` 되지 않은 함수
- 같은 디렉토리 안에서만 사용되는 헬퍼

이름이 같아도 🟢 참고로만 표시한다.

### 4. 외부 라이브러리 wrapper

```
기존: utils/lodash.debounce를 단순 re-export
신규: 직접 debounce 구현
```

wrapper 자산은 책임이 외부 라이브러리에 종속. 책임 변경이 일어날 수 있어 재사용 강도를 낮춘다.

### 5. 테스트 fixture / mock

```
__mocks__/, fixtures/, test-utils/ 하위 자산
```

테스트 전용 자산은 운영 코드 재사용 대상이 아니다. 무조건 🟢 참고로 분류.

---

## false negative 방지 (중복 놓치지 않기)

다음 케이스는 이름이 달라도 **시그니처·책임을 비교**한다.

### 1. 네이밍 컨벤션 차이

```
기존: format_date_ko(date)
신규: formatDateKo(date)
신규: dateFormatKo(date)
```

snake/camel/kebab 변형은 동일 후보로 본다. 키워드 분해해 부분 일치 검색.

### 2. 약어/풀이형 혼용

| 약어 | 풀이형 |
|------|--------|
| `dto` | `dataTransferObject` |
| `req` | `request` |
| `res` | `response` |
| `usr` | `user` |
| `cfg` | `config` |

둘 다 검색 키워드에 포함.

### 3. 동의어

| 검색어 | 함께 볼 동의어 |
|--------|--------------|
| `create` | `add`, `new`, `register`, `insert` |
| `update` | `edit`, `modify`, `patch` |
| `delete` | `remove`, `destroy` |
| `get` / `fetch` | `load`, `find`, `read`, `query` |
| `card` | `tile`, `item`, `box` |
| `list` | `table`, `grid`, `index` |

신규 자산 이름이 `createUser`면 `addUser`/`registerUser`도 함께 검색.

### 4. 약간 다른 prefix/suffix

- `User` vs `UserModel` vs `UserEntity`
- `useUser` vs `useUserQuery` vs `useUserData`
- `SearchResultCard` vs `ResultCard` vs `SearchCard`

prefix/suffix 제거 후 핵심 어간으로 비교.

---

## "신규 권장"이 자연스러운 케이스

다음 상황은 발견되더라도 **신규 생성이 자연스러움**. 리포트에 명시한다.

- 책임 도메인이 명확히 다름
- 기존 자산이 단일 책임 원칙을 이미 다 채우고 있어 확장 시 SRP 위반
- 기존 자산이 외부 lib에 강하게 결합되어 의존성 추가 비용이 큼
- 기존 자산이 곧 제거 예정 (todo/migration 주석)

---

## 사용자에게 설명할 표현

매칭 근거를 보고할 때 다음 표현을 권장한다:

✅ 좋은 표현:
- "이름·필드 3/3 일치 + 같은 도메인 디렉토리 → 재사용 강력 후보"
- "props 3개 겹침, 신규 2개 추가 필요 → 옵셔널 props로 확장 가능"
- "이름은 같지만 `billing` vs `marketing` 도메인 → 재사용 비권장"

❌ 피할 표현:
- "비슷해 보임"
- "같을 수도 있음"
- "체크 필요"

근거를 구체적으로 적어야 사용자가 결정하기 쉽다.
