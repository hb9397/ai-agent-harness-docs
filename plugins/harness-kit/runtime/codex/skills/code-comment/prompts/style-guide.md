# 언어별 주석 스타일 가이드 (style-guide)

## 감지 우선순위

확장자 확인 후 아래 표에서 **해당 언어 섹션만** 읽는다.

| 확장자 | 추가 감지 조건 | 적용 섹션 |
|--------|---------------|-----------|
| `.tsx` `.jsx` | JSX 문법 포함 | [JS/TS] + JSX 화면 요소 |
| `.ts` `.js` | package.json 내 프레임워크 확인 | [JS/TS] |
| `.py` | requirements.txt / pyproject.toml 확인 | [Python] |
| `.java` | pom.xml 존재 여부 | [Java] |
| `.kt` | build.gradle.kts 존재 여부 | [Java] 섹션 준용 |

---

## [JS/TS] JavaScript · TypeScript · React · Next.js

### 파일 최상단
```ts
/**
 * [파일명] UserService.ts
 * [기능]   사용자 인증 및 계정 관리 (비밀번호 해싱, JWT 발급, 세션 갱신 등 핵심 비즈니스 로직)
 * [역할]   컨트롤러에서 전달된 사용자 정보를 기반으로 DB 검증을 수행하고, 성공 시 액세스/리프레시 토큰 페어를 생성하여 반환한다.
 * [export] UserService 클래스
 */
```

### 클래스·메서드·훅
```ts
/**
 * 사용자 로그인 처리 메서드
 * 이메일·비밀번호 검증 후 JWT 액세스/리프레시 토큰을 발급한다.
 * @param email    사용자 이메일
 * @param password 평문 비밀번호 (내부에서 bcrypt 비교)
 * @returns        액세스 토큰, 리프레시 토큰
 */
async login(email: string, password: string) {
  // 1. 이메일로 사용자 조회
  // 2. 비밀번호 해시 비교
  // ⚠️ 검증 실패 시 즉시 예외 — 이후 로직 실행 금지
  // 3. 토큰 생성 및 반환
}
```

### 변수
```ts
const MAX_RETRY = 3        // 최대 재시도 횟수
const isLoggedIn = false   // 현재 로그인 여부
```

### JSX 화면 요소
```tsx
{/* 로그인 폼 — 이메일·비밀번호 입력 및 제출 */}
<form onSubmit={handleSubmit}>
  {/* 이메일 입력 필드 */}
  <input type="email" />
  {/* 로그인 제출 버튼 */}
  <button type="submit">로그인</button>
</form>
```

### 파일 최하단 변경 이력
```ts
/*
 * [최종 수정]
 * 작성자: hong@example.com
 * 날짜:   {YYYY-MM-DD}
 * 변경:   로그인 실패 횟수 초과 시 계정 잠금 로직 추가
 */
```

---

## [Python] Python · FastAPI · Django · Flask

### 파일 최상단
```python
"""
[파일명] user_router.py
[기능]   사용자 계정 관리 API 라우터 (회원가입, 로그인, 프로필 조회 기능 제공)
[역할]   POST /users (회원가입), POST /users/login (인증 토큰 발급), GET /users/me (프로필 조회) 엔드포인트를 등록하고 HTTP 요청 파라미터를 검증한다.
[export] user_router 객체 (FastAPI APIRouter)
"""
```

### 클래스·메서드
```python
class UserService:
    """
    사용자 인증 서비스 클래스
    DB 조회·비밀번호 검증·토큰 발급 등 도메인 핵심 로직을 담당한다.
    Repository 레이어를 외부에 의존성을 두고 주입받아 사용한다.
    """

    async def login(self, email: str, password: str):
        """
        사용자 로그인 처리
        이메일·비밀번호 검증 후 JWT 토큰을 반환한다.
        """
        # 1. 이메일로 사용자 조회
        # 2. 비밀번호 해시 비교
        # ⚠️ 검증 실패 시 즉시 예외 — 이후 로직 실행 금지
        # 3. 토큰 생성 및 반환
```

### 변수
```python
MAX_RETRY = 3        # 최대 재시도 횟수
is_logged_in = False # 현재 로그인 여부
```

### 파일 최하단 변경 이력
```python
# ----------------------------
# [최종 수정]
# 작성자: hong@example.com
# 날짜:   {YYYY-MM-DD}
# 변경:   로그인 실패 횟수 초과 시 계정 잠금 로직 추가
# ----------------------------
```

---

## [Java] Java · Spring Boot

### 파일 최상단
```java
/**
 * [파일명] UserController.java
 * [기능]   사용자 계정 관리 REST API 제어 (회원가입, 인증, 프로필 조회)
 * [역할]   POST /api/v1/users/login (로그인), POST /api/v1/users/signup (회원가입) 엔드포인트를 제공하고 클라이언트 요청 파라미터를 검증하여 UserService로 전달한다.
 * [Bean]   @RestController — Spring 컨테이너에 의해 싱글톤 관리
 */
```

### 클래스·메서드
```java
/**
 * 사용자 로그인 처리 메서드
 * 이메일·비밀번호 검증 후 JWT 액세스/리프레시 토큰을 발급한다.
 *
 * @param email    사용자 이메일
 * @param password 평문 비밀번호
 * @return         TokenResponse (액세스 토큰, 리프레시 토큰)
 */
public TokenResponse login(String email, String password) {
    // 1. 이메일로 사용자 조회
    // 2. 비밀번호 해시 비교
    // ⚠️ 검증 실패 시 즉시 예외 — 이후 로직 실행 금지
    // 3. 토큰 생성 및 반환
}
```

### 변수
```java
private static final int MAX_RETRY = 3;  // 최대 재시도 횟수
private boolean isLoggedIn = false;       // 현재 로그인 여부
```

### 파일 최하단 변경 이력
```java
/*
 * [최종 수정]
 * 작성자: hong@example.com
 * 날짜:   {YYYY-MM-DD}
 * 변경:   로그인 실패 횟수 초과 시 계정 잠금 로직 추가
 */
```
