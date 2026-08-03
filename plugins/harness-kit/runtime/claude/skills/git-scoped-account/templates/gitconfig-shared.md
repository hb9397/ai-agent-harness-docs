# templates/gitconfig-shared.md
# 역할: 상위 디렉토리에 생성하는 공통 git config 파일의 구조
# 사용법: 아래 구조로 실제 파일(.gitconfig-scoped 등)을 만든다. 주석 줄은 최종 파일에서 제거한다.
# 주의: 예시 데이터를 넣지 않는다. 값은 [입력 수집]에서 받은 실제 값으로 채운다.

[user]
    name = <user.name>
    email = <user.email>

<!-- 토큰·비밀번호·credential username은 넣지 않는다 (이 스킬은 user 정보만 관리) -->
