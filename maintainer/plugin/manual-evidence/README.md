# 수동 표면 증적 보관소

완료한 표면 증적을 `YYYYMMDD/{surface}.md`로 저장한다. 양식은
`maintainer/plugin/manual-surface-test-template.md`를 복사해서 쓴다.

```text
manual-evidence/
└── 20260801/
    ├── codex-cli.md
    ├── codex-desktop-app.md
    ├── claude-code-cli.md
    └── claude-desktop-code.md
```

## 판정 규칙

- 자동 설치 smoke를 실제 모델 동작 성공으로 대신하지 않는다.
- CLI 성공을 앱 성공으로 대신하지 않는다.
- 지원되지 않는 앱 표면은 `SKIP`이 아니라 근거가 있는 `미지원`으로 기록한다.
- 증적은 **설치한 payload 버전과 함께** 기록한다. 버전이 다르면 이전 결과를
  이어받지 않는다. `verify_install_surfaces.py`가 이 불일치를 검사한다.
- 네 표면의 수동 증적이 모두 충족되기 전에는 release-ready로 표시하지 않는다.

## 현재 상태 — `0.2.0`

| 표면 | 상태 | 근거 |
|---|---|---|
| Codex CLI | `blocked` | CLI 미설치 환경. `0.1.0` smoke 증적은 버전 불일치로 무효. |
| Codex Desktop/App | `manual-required` | 대화형 앱 표면이 필요하다. |
| Claude Code CLI | `blocked` | 위와 같음. |
| Claude Desktop Code | `manual-required` | Desktop 앱 표면이 필요하다. |

`0.1.0`에서 수행한 CLI 설치 smoke는 Codex CLI `0.146.0`, Claude Code `2.1.220`
기준이며 `0.2.0`에는 적용되지 않는다. 스킬이 18종에서 20종으로 늘고 archive가
바뀌었으므로 재실행이 필요하다.

## 재실행 절차

CLI가 설치된 환경에서 관리 저장소 루트를 기준으로 실행한다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/smoke_cli_install.py
```

성공하면 `maintainer/plugin/cli-smoke.json`이 새 payload 버전으로 갱신된다.
이어서 증적을 다시 생성하고 검사한다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py
python maintainer/skills/harness-plugin-maintainer/scripts/verify_install_surfaces.py --check
```

CLI 없이 payload 계약만 확인하려면 오프라인 self-test를 쓴다. 이것은 설치
증적이 아니다.

```bash
python maintainer/skills/harness-plugin-maintainer/scripts/smoke_cli_install.py --self-test
```
