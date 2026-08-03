# Maintainer Area

이 디렉터리는 `harness-kit` 관리자가 사용자 플러그인을 만들고 갱신하기 위해 사용하는 repo-local 원본 영역이다.

## 원칙

- 별도의 관리자 플러그인은 만들지 않는다.
- 관리자 스킬 정본은 `maintainer/skills/`에 둔다.
- `.agents/skills/`와 `.claude/skills/`는 `maintainer/skills/`에서 생성되는 projection이다.
- 사용자 플러그인 payload는 `skills/` 정본에서 생성한 `plugins/harness-kit/`로 구성한다.
- 관리자 스킬은 사용자 플러그인 source 목록에 포함하지 않는다.

관리자는 별도 관리자 플러그인을 설치하지 않는다. 이 저장소에서는 repo-local 관리자
projection으로 유지보수 작업을 수행하고, 사용자와 같은 설치 표면을 검증할 때만
`harness-kit` 사용자 플러그인을 별도 격리 설정에 설치한다. 관리자 projection과
사용자 플러그인 cache를 같은 디렉터리에 합치지 않는다.

## 관리자 스킬

- `custom-skill-design`: 관리자용 스킬 설계·개선
- `skill-portfolio-maintainer`: 사용자 스킬 포트폴리오와 외부 upstream 관리
- `harness-plugin-maintainer`: Codex·Claude 사용자 플러그인 생성, 검증, 릴리스 관리

## Projection

관리자 projection은 다음 명령으로 갱신한다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py
```

drift만 확인하려면 다음 명령을 사용한다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/sync_manager_projections.py --check
```

projection에는 관리자 3종만 포함한다. `harness-setup` 등 사용자 스킬은 projection에 두지 않는다.
