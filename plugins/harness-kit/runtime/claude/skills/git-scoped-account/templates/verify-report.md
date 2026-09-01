# templates/verify-report.md
# 역할: Step 5 검증 리포트의 출력 구조
# 사용법: 아래 표 구조로 대화창에 출력한다. 예시 데이터는 넣지 않는다.

## 적용 검증 결과

상위 디렉토리: <base path>
공통 config: <shared config path>

| # | repo | user.name | user.email | 출처 | provider / host / account | 문서 권한 로컬 등록 | 판정 |
|---|------|-----------|------------|------|---------------------------|----------------------|------|
<!-- 출처가 공통 config 파일이고 로컬 표식 5개가 정확히 하나씩 있으면 ✅, 전역 ~/.gitconfig 또는 표식 누락이면 ⚠️ -->
<!-- 예시: | 1 | repo-api | <name> | <email> | .gitconfig-scoped | github / github.com / @login | 적용·미적용·정책 없음 | ✅ | -->

요약: 정상 N개 / 경고 M개
<!-- 경고가 있으면 원인(예: include 미적용, 로컬 user 설정이 override)과 조치를 한 줄로 덧붙인다 -->
