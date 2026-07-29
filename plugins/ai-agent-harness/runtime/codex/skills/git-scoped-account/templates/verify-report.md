# templates/verify-report.md
# 역할: Step 5 검증 리포트의 출력 구조
# 사용법: 아래 표 구조로 대화창에 출력한다. 예시 데이터는 넣지 않는다.

## 적용 검증 결과

상위 디렉토리: <base path>
공통 config: <shared config path>

| # | repo | user.name | user.email | 출처 | 판정 |
|---|------|-----------|------------|------|------|
<!-- 출처가 공통 config 파일이면 ✅, 전역 ~/.gitconfig면 ⚠️ -->
<!-- 예시: | 1 | repo-api | <name> | <email> | .gitconfig-scoped | ✅ | -->

요약: 정상 N개 / 경고 M개
<!-- 경고가 있으면 원인(예: include 미적용, 로컬 user 설정이 override)과 조치를 한 줄로 덧붙인다 -->
