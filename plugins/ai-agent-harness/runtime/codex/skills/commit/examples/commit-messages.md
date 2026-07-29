# 커밋 메시지 예시

## 좋은 예시

```
feat(auth): 소셜 로그인 기능 추가

카카오/네이버 OAuth2 연동. 기존 이메일 로그인과 병행 지원.
```

```
fix(order): 주문 취소 시 재고 미복구 버그 수정

cancelOrder에서 stockService.restore 호출 누락.
동시 취소 시 race condition 방지를 위해 비관적 락 적용.
```

```
refactor(domain): Member 엔티티 Builder 패턴으로 전환

생성자 파라미터 6개 초과로 가독성 저하.
@Builder + 정적 팩토리 메서드 조합으로 변경.
```

```
test(payment): 결제 금액 경계값 테스트 추가

0원, 음수, 최대값(999_999_999) 케이스 검증.
```

## 나쁜 예시

```
# 영어 description (프로젝트 규칙: 한글)
feat(auth): add social login

# scope 누락
feat: 소셜 로그인 추가

# "무엇을"만 (why가 없음)
fix(order): cancelOrder 메서드 수정

# 50자 초과
feat(auth): 카카오와 네이버 소셜 로그인 OAuth2 연동 기능을 추가하고 기존 이메일 로그인과 병행 지원

# 여러 성격 혼합 (분리 필요)
feat(auth): 소셜 로그인 추가 및 기존 로그인 버그 수정
```

## scope 결정 방법

git diff에서 변경된 파일 경로의 최상위 디렉토리 또는 핵심 모듈명을 사용한다.

| 변경 파일 경로 예시 | 적절한 scope |
|-------------------|-------------|
| src/auth/login.ts | auth |
| components/Button.jsx | ui |
| api/users/route.ts | api |
| scripts/deploy.sh | ci |
| package.json, requirements.txt | deps |
| README.md, docs/ | docs |

프로젝트 고유 scope (예: 도메인명)는 CLAUDE.md에서 확인한다.
