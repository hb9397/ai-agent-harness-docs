# 멀티 리뷰 결과 보고서 템플릿

리뷰 완료 후 아래 형식으로 결과를 출력하세요.

---

## 📋 요약

| 항목 | 값 |
|------|-----|
| 변경 파일 수 | N개 |
| 🔴 Critical | N건 |
| 🟠 Major | N건 |
| 🟡 Minor | N건 |
| 💡 Suggestion | N건 |

## 🔍 발견 목록

| # | 심각도 | 관점 | 파일 | 설명 |
|---|--------|------|------|------|
| 1 | 🔴 | Security | `src/auth.ts:23` | SQL 인젝션 가능 — 파라미터 바인딩 필요 |
| 2 | 🟠 | Performance | `src/user.service.ts:45` | N+1 쿼리 — join fetch 또는 batch 로딩 필요 |
| 3 | 🟡 | Maintainability | `src/order.controller.ts:12` | 메서드 80줄 — SRP 위반, 분리 권장 |
| 4 | 💡 | Testing | `src/payment.ts:30` | 경계값 테스트 누락 — 0원, 음수 케이스 추가 권장 |

## 심각도 기준

- 🔴 **Critical**: 보안 취약점, 데이터 유실 위험, 운영 장애 가능 (반드시 수정)
- 🟠 **Major**: 성능 저하, 중요 로직 결함, 확장성 문제 (강력 권고)
- 🟡 **Minor**: 코드 품질, 가독성, 유지보수성 (개선 권장)
- 💡 **Suggestion**: 테스트 보강, 리팩토링 아이디어 (참고)

## ✅ 통과 항목

- ✅ Security: 인젝션 취약점 없음
- ✅ Performance: 불필요한 반복 없음
- ✅ ...
