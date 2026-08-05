# UI/UX Pro Max v2.13.0 license·security 검토 보고서

| 항목 | 결과 |
|---|---|
| 검토 대상 | `v2.11.3` `4857a2c5ef989794751a0f66b8545a4a49566286` → `v2.13.0` `4d140cf8ff6842de13213c7214eff3810371beb2` |
| 판정 | `accept-for-staging` |
| G2 license/security | 통과 |
| G4 보호 자산 | promotion 전 명시 승인 필요 |
| G5 파괴적 변경 | 불필요 (`destructive_changes=[]`) |

## License

Git `core.autocrlf`를 끈 raw archive bytes로 두 tag의 `LICENSE`를 비교했다. 전문, SPDX
`MIT`, `Copyright (c) 2024 Next Level Builder` 표기가 같으며 SHA-256은 모두
`738f69dfa83db5c347c678fb9d90e560877059f0de93a327c39001bff92dc014`다. 이 값은 현행
accepted provenance, registry, NOTICE의 기록과도 일치한다. license block 사유는 없다.

## 실행 표면

target generated skill의 scripts import root는 Python 표준 라이브러리와 local
`core`, `design_system`뿐이다. 정적 검사에서 network client, subprocess·shell 호출,
`eval`·`exec`·dynamic import는 발견되지 않았다. 외부 패키지 설치나 host API도 없다.

filesystem write는 기존 `persist_design_system()`의 `mkdir`와 Markdown `write_text`뿐이며,
이번 upstream 변경이 추가한 기능이 아니다. runtime-preview의 local `SKILL.md`는 저장을
명시적 사용자 요청으로 제한하고 `--output-dir`을 프로젝트 `.docs/`로 지정하도록 하며,
기존 파일은 먼저 읽어 diff를 확인하고 무승인 overwrite를 금지한다. script 단독의
`--output-dir` 인자는 이 local runtime 계약 아래에서만 호출한다.

변경분은 `scripts/design_system.py`의 dark-mode palette/anti-pattern 계산과
`scripts/tests/test_design_system_mode.py`의 unit test다. new code가 실행 권한, 입력 경로,
network, subprocess, persistent write 범위를 넓히지 않는다.

## 검증과 회귀 경계

runtime-preview에서 다음을 실행했고 36개 test가 모두 통과했다.

```text
python -m unittest discover -s scripts/tests -v
```

기대 이익은 dark-mode 요청에서 palette와 anti-pattern 판단의 정합성 향상이다. 남는 회귀
위험은 해당 요청의 palette 선택이 달라질 수 있다는 동작 변화이며, 새 unit test와 기존
test suite가 그 경계를 검증한다.

## 플랫폼·승인 결론

Codex와 Claude Code는 각각 `runtime/codex/skills/**`, `runtime/claude/skills/**`에서 같은
canonical payload를 사용한다. 호출 이름은 다를 수 있지만 이번 candidate의 Python 의존성,
권한, write 계약에는 차이가 없다. plugin build 및 실제 앱·CLI 모델 호출 smoke는 아직
수행하지 않았다.

G2는 통과했다. 보호 script/test 두 파일을 canonical로 promotion하려면 G4 자산 영향 승인
ID가 필요하다. 삭제·이동이 없으므로 G5는 요구하지 않는다. G3 일반 적용 승인도 promotion
handoff 전까지는 발급하지 않는다.
