# 카테고리별 코드베이스 스캔 패턴 (scan-patterns)

각 자산 카테고리를 코드베이스에서 찾는 패턴 정의.
grep + glob 기반. AST 없이 표면 매칭만 수행한다.

---

## 공통 스캔 우선 디렉토리

다음 디렉토리는 카테고리 무관하게 우선 스캔한다:

```
common/      shared/       lib/         utils/
dto/         schemas/      types/       models/
entities/    api/          routers/     handlers/
components/  hooks/        stores/      atoms/
```

존재하지 않으면 무시한다.

---

## BE 스캔

### API 라우트

```
검색 도구: Grep
패턴 예시:
  - FastAPI/Express:  "@app\\.(get|post|put|delete)" + path 키워드
  - NestJS:           "@Controller|@Get|@Post" + path 키워드
  - Spring:           "@RequestMapping|@GetMapping" + path 키워드
글로브:   **/*.{py,ts,js,java,go,rb}
출력:     파일:줄 + 라우트 정의 본문 1줄
```

비교 기준: HTTP method + path. path는 변수 파라미터를 placeholder로 정규화한 뒤 비교한다 (`/users/:id` ↔ `/users/{id}`).

### DTO / 스키마

```
패턴:
  - Pydantic:    "class\\s+{Name}\\(BaseModel\\)"
  - TypeScript:  "(interface|type)\\s+{Name}"
  - Java:        "class\\s+{Name}.*DTO"
  - dataclass:   "@dataclass.*class\\s+{Name}"
글로브:   **/{dto,schemas,types,models}/**
보조 검색: 필드명 3개 이상 일치하는 클래스
```

이름이 정확히 같지 않아도 **필드 집합이 60% 이상 겹치면 🟡 유사** 후보.

### Entity / 모델

```
패턴:
  - SQLAlchemy:  "class\\s+{Name}\\(Base\\)" + "__tablename__"
  - Prisma:      "model\\s+{Name}\\s*\\{"
  - TypeORM:     "@Entity.*class\\s+{Name}"
  - Django:      "class\\s+{Name}\\(models\\.Model\\)"
글로브:   **/{models,entities}/**, **/schema.prisma
```

테이블명/컬럼명도 비교 대상에 포함한다.

---

## FE 스캔

### 컴포넌트

```
패턴:
  - 함수형:     "(export\\s+)?(default\\s+)?function\\s+{Name}"
              "const\\s+{Name}\\s*[:=].*=>"
  - 클래스형:   "class\\s+{Name}\\s+extends.*Component"
글로브:   **/components/**/*.{tsx,jsx,vue,svelte}
보조 검색:
  - 파일명 기준: components/**/{Name}.* 또는 components/**/{Name}/index.*
```

`SearchResultCard` 찾을 때 `ResultCard`, `Card`, `SearchCard`도 후보로 잡아 🟡 분류.

### 훅

```
패턴:
  - "(export\\s+)?(const|function)\\s+use{Name}"
  - 파일명: hooks/use{Name}.*
글로브:   **/hooks/**, **/use*.{ts,tsx,js,jsx}
```

이름 prefix `use` 누락 케이스도 검색하되 결과는 🟡로만 분류.

### 페이지 / 라우트

```
패턴:
  - Next.js App Router:  app/**/page.{tsx,jsx}
  - Next.js Pages:       pages/**/*.{tsx,jsx}
  - React Router:        "Route.*path=" 키워드
  - Vue Router:          "path:\\s*['\"]" 키워드
```

라우트 path 비교는 placeholder 정규화 후 수행.

### 상태 스토어

```
패턴:
  - Redux:     "createSlice|combineReducers"
  - Zustand:   "create\\(.*=>.*\\{"
  - Recoil:    "atom\\(\\{"
  - Jotai:     "atom\\("
글로브:   **/{stores,atoms,slices}/**
```

상태 키 이름 매칭으로 중복 가능성 추론.

---

## 공통 스캔

### 유틸 함수

```
패턴:
  - "(export\\s+)?(const|function)\\s+{name}"
글로브:   **/{utils,lib,helpers}/**/*.{ts,js,py}
```

`formatDate`/`format_date`/`dateFormat` 같은 변형 케이스를 위해
**키워드를 분해해 부분 일치 검색**한다 (`format` + `date`).

### 상수 / enum

```
패턴:
  - "export\\s+const\\s+{NAME}"
  - "enum\\s+{Name}"
  - "{NAME}\\s*=\\s*['\"]"
글로브:   **/{constants,enums}/**
```

값 종류가 거의 같으면 🔴 동일, 일부 겹치면 🟡 유사.

### i18n 키

```
패턴:
  - 키 prefix 검색: "{prefix}\\." in **/*.{json,yaml,po}
글로브:   **/locales/**, **/i18n/**
```

---

## 스캔 호출 제어

- **카테고리당 grep 1~3회**로 제한.
- 결과 30건 초과 시 상위 후보만 표시하고 "더 보기" 옵션 제시.
- 작업지침서에서 디렉토리가 좁혀지면 그 디렉토리부터 먼저 스캔.

---

## 줄 번호와 시그니처 추출

매칭된 결과는 항상 다음 형식으로 정규화한다:

```
{relative-path}:{line}  {1줄 시그니처}
```

예시:
```
backend/dto/site.py:12  class CreateSite(BaseModel):
frontend/src/utils/date.ts:8  export function formatKo(date: Date): string
```

복수 줄 시그니처는 1줄로 줄여 출력한다.
