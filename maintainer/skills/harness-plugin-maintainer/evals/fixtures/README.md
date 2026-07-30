# Harness Plugin Maintainer 픽스처

플러그인 페이로드가 사용자 스킬셋의 정본이므로 Phase 6 평가는 현재 저장소
소스를 기준으로 빌드한다. 격리된 출력 루트(`output-root`) 픽스처는 플러그인
드리프트를 주입하고, `build_plugin.py --check`가 드리프트가 발생한 정본
파일을 다시 쓰지 않으면서 이를 감지하는지 검증한다. `validate_plugin.py`는
매니페스트, 저장소 루트 마켓플레이스, LF 정규화, 아카이브 모드, 체크섬,
패키징된 업스트림 폐쇄 조건의 실패 사례를 다룬다.

`smoke_cli_install.py --self-test`는 네트워크 접근 없이 생성된 두 런타임
페이로드를 검증한다. CI에서는 공식 CLI로 격리된 Codex 및 Claude
마켓플레이스의 `add/install/list/remove` 전체 수명주기를 별도로 실행한다.
