# 스킬 업스트림 업데이트 정책

이 저장소는 참조 전용 학습과 업스트림 직접 반입을 분리한다.

## 출처 분류 및 모드

| 모드 | 의미 | 필수 처리 |
|---|---|---|
| `native` | 로컬에서 작성했으며 활성 외부 출처 관계가 없음 | 일반 저장소 리뷰 |
| `reference` | 외부 출처가 개념에만 영향을 줌 | 출처 URL과 내부 반영 지점 기록 |
| `vendored` | 업스트림 파일을 원문 그대로 복사함 | 라이선스, NOTICE, 해시, 파일 매핑, 승인 |
| `adapted` | 업스트림 콘텐츠를 번역·수정·재구성함 | `vendored`와 동일한 항목에 로컬 패치·처리 기록 추가 |
| `unknown` | 증거가 불충분함 | 해결될 때까지 반입 또는 릴리스 금지 |

## 상태 모델

| 상태 | 의미 |
|---|---|
| `observed` | 읽기 전용 검토에서 확인한 최신 릴리스, 태그, 브랜치 또는 문서 상태 |
| `accepted` | 통합 후보로 관리자가 승인한 업스트림 ref |
| `embedded` | 출처가 사용자 정본 `skills/` 또는 관리자 정본 `maintainer/skills/`에 반영된 상태 |
| `packaged` | 출처가 검증된 플러그인 산출물에 포함된 상태 |
| `released` | 출처가 릴리스된 플러그인 버전을 통해 사용자에게 제공되는 상태 |

참조 출처는 검토일과 선택적 ref를 사용한다. 직접 반입은 `accepted` 전에 변경 불가능한 SHA와 파일 해시가 필요하다.

GitHub 저장소의 기본 브랜치 SHA가 바뀌었다고 해서 감시 대상 스킬 파일이 바뀐 것은
아니다. 정확한 경로를 등록한 출처는 다음처럼 branch/release와 watched path의 마지막
변경을 함께 확인한다. glob 경로는 GitHub API에서 경로 단위로 해석하지 않고
source-level SHA와 후속 의미 diff로 판정한다.

```bash
python maintainer/skills/skill-portfolio-maintainer/scripts/check_upstreams.py --source openai-codex-skill-creator --verify-watched-paths
```

`--write-observed` 없이 실행하면 읽기 전용이다. 이 결과도 최신 파일의 자동 반입이나
`accepted` 승격을 뜻하지 않는다.

exact watched path 중 하나라도 rate limit·네트워크·API 오류가 발생하면 새 path 관측
묶음 전체를 lock에 저장하지 않는다. 직전의 완전한 path 관측이 있으면 그대로 보존하고,
없으면 source-level ref·SHA와 불완전 사유만 기록한다. 일부 성공 결과만 섞어서
“경로 검증 완료”로 표시하지 않는다.

## 승인 게이트

| 게이트 | 요구 사항 |
|---|---|
| G0 | 출처 등록과 의도한 모드 승인 |
| G1 | 관리자 신원, 릴리스, 태그 및 전체 SHA 검증 |
| G2 | 라이선스 및 서드파티 콘텐츠 검토 |
| G3 | 스크립트, 훅, MCP, 네트워크, 바이너리, 심볼릭 링크, 서브모듈 및 권한 검토 |
| G4 | 보호 자산 영향을 포함한 개념 또는 파일 범위 승인 |
| G5 | 삭제·이동·교체에 대한 별도의 파괴적 변경 승인 |
| G6 | 승격 전 임시 스테이징에만 적용 |
| G7 | Codex, Claude, 회귀 및 라이선스 검증 |
| G8 | 정본 출처로 승격하고 플러그인 릴리스 흐름에 인계 |

“최신 버전으로 업데이트”라는 표현만으로는 G4 또는 G5 승인이 되지 않는다.

### 하나의 upstream에서 파생된 여러 관계

같은 저장소를 직접 반입과 참고로 동시에 추적할 때, 두 관계는
`relationship_group`으로 묶고 **하나의 candidate로 원자적으로 승인·승격**한다.

- 그룹 안의 저장소 URL, `source_url`, `license_spdx`, `lifecycle`,
  observed·accepted SHA는 모두 일치해야 한다.
- 한쪽만 새 SHA로 올리거나 한쪽만 `active`로 바꾸는 요청은 차단한다.
- 서로 다른 upstream을 하나의 candidate에 섞지 않는다.
- 조사와 staging은 여전히 GitHub upstream 하나씩 수행한다.

보고서에는 직접 반입 관계의 **파일 diff·hash·라이선스**와 참고 관계의 **의미 단위
차이**를 구분해 적는다. protected asset 영향과 destructive diff도 관계별·파일별로
나눈다.

## 보호 자산

보호 대상 경로는 다음과 같다.

- `scripts/`
- `templates/`
- `assets/`
- `references/`
- `prompts/`
- `agents/`
- `commands/`
- `hooks/`
- `bin/`
- `example/`, `examples/`
- `evals/`, `tests/`
- 플러그인 manifest 및 MCP/LSP 설정
- `LICENSE*`, `NOTICE*`

보호 자산을 추가하거나 수정하려면 자산 영향 기록이 필요하다. 보호 자산을 삭제·이동·교체하려면 별도의 파괴적 변경 승인이 필요하다.

## 관리자 스킬 책임 경계

`skill-portfolio-maintainer`는 업스트림 탐색, 출처 분류, 레지스트리 업데이트 및 보호 자산 영향 분석을 담당한다.

`harness-plugin-maintainer`는 Codex 및 Claude 플러그인 런타임 생성, manifest 생성, 패키징, 스모크 테스트 및 릴리스 산출물을 담당한다.

두 책임은 분리되어야 한다. 출처는 패키징하지 않고도 분류할 수 있으며, 플러그인 패키지에는 승인되지 않았거나 차단된 업스트림 파일을 포함해서는 안 된다.

## 롤백

모든 직접 반입 승격에는 이전 잠금 상태, 승인된 ref, 파일 매핑, 생성된 해시 및 검증 결과가 포함되어야 한다. 롤백은 이전 잠금 상태와 승격된 파일을 복원한 다음 레지스트리 및 플러그인 검사를 다시 실행하는 것을 의미한다.
