# 생성 의도 추출 규칙 (extract-intents)

작업지침서 또는 자유 텍스트에서 **이 작업이 만들 예정인 자산**을 뽑는다.

---

## 입력 위치별 추출 포인트

### impl-doc / impl-fe-be-doc 산출물

- 각 태스크의 `(파일 경로)` 필드 → 생성 파일
- `**구현 내용**` 본문 → 자산 이름·시그니처 단서
- `**Agent 지시**` 본문 → 함수/클래스 시그니처 명시
- 화면 중심 Phase의 "컴포넌트 트리" → FE 컴포넌트 후보
- "API 연동 표" → API 엔드포인트 후보
- "상태 관리 표" → 훅·스토어 후보

### 자유 텍스트

사용자 발화에서 다음 표현을 캐치한다:
- "{이름} 컴포넌트 만들" → 컴포넌트 후보
- "POST /api/{path}" → 라우트 후보
- "{Name}DTO" / "{Name}Request" / "{Name}Schema" → DTO 후보
- "{name} 훅" / "use{Name}" → 훅 후보
- "format/parse/convert/validate {something}" → 유틸 후보

---

## 카테고리별 추출 항목

```
[BE]
  - API 라우트: method + path
  - 핸들러 함수: 이름, 입출력 타입
  - DTO/스키마: 이름, 필드 목록
  - Entity/모델: 이름, 컬럼, 관계
  - 마이그레이션: 테이블, 컬럼 변경

[FE]
  - 컴포넌트: 이름, props 시그니처
  - 페이지/라우트: 경로
  - 훅: 이름, 반환 타입
  - 상태 스토어: 이름, 상태 키
  - 타입: 이름, 필드

[공통]
  - 유틸 함수: 이름, 시그니처
  - 상수/enum: 이름, 값 종류
  - i18n 키: 키 prefix
  - 디자인 토큰: 색·간격·타이포 변수
```

---

## 추출 결과 형식

내부적으로 다음 구조로 정리한다 (사용자에게 보이지 않아도 됨):

```yaml
intents:
  - category: BE
    type: DTO
    name: CreateSite
    signature: "{name: str, url: HttpUrl, owner_id: int}"
    source_task: BE-03
    source_file: backend/dto/sites.py

  - category: FE
    type: Component
    name: SearchResultCard
    signature: "{title, url, snippet}"
    source_task: FE-05
    source_file: frontend/src/components/SearchResultCard.tsx
```

이 구조를 다음 Step의 스캔 입력으로 사용한다.

---

## 추출 우선순위

태스크가 많을 때는 다음 순서로 우선 추출한다:

1. **외부에 노출되는 자산** (API, public 컴포넌트, export 함수)
2. **여러 곳에서 사용될 가능성** (DTO, 공통 컴포넌트, 유틸)
3. **도메인 모델** (Entity, 핵심 타입)
4. 기타 내부 헬퍼

추출 항목이 20개를 넘으면 1~3 범주만 다루고 사용자에게 알린다.

> "추출된 자산 후보가 N개입니다.
> 외부 노출·공유 가능성이 높은 상위 X개만 우선 스캔할까요?"
