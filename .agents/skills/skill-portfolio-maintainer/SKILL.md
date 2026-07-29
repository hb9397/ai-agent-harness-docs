---
name: skill-portfolio-maintainer
description: "관리자가 사용자 스킬 포트폴리오의 외부 공식·유명 스킬 참고 관계, provenance, protected asset 영향, upstream 최신화 후보를 조사하고 반영 계획을 관리할 때 사용한다. 사용자 플러그인 패키징이나 릴리스 생성은 담당하지 않는다."
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Skill Portfolio Maintainer

사용자 스킬셋의 품질과 provenance를 관리하는 관리자 전용 스킬이다.

## 책임

- `skills/` 사용자 스킬의 upstream 관계를 `native`, `reference`, `adapted`, `vendored`로 분류한다.
- 공식 스킬, 외부 유명 스킬, GitHub release를 조사해 반영 후보를 만든다.
- protected asset, templates, scripts, examples 변경 영향을 분리한다.
- 삭제·이동·교체가 필요한 경우 별도 파괴적 변경 승인 항목으로 분리한다.

## 비책임

- Codex·Claude 플러그인 manifest 생성
- 사용자 플러그인 release archive 생성
- `.agents/skills` 또는 `.claude/skills` projection 생성

## 운영 원칙

- 사용자가 “최신화”라고만 말해도 canonical source를 바로 수정하지 않는다.
- `check`와 `discover`는 읽기 전용이다. `observed` 외 lock 상태(`accepted`, `embedded`, `packaged`, `released`)를 변경하지 않는다.
- `promote`는 한 upstream/candidate씩 수행한다.
- protected asset 추가·수정·보완은 별도 asset-impact approval이 필요하다.
- 삭제·이동·교체는 별도 destructive approval이 필요하다.
- license 변경, 불명확한 재배포 권리, scripts/hooks/MCP/network 권한 확대, path traversal, symlink, submodule, binary/LFS 의심은 차단한다.
- 이 스킬 자신의 upstream·본문을 갱신하는 self-update는 같은 session에서 promote하지 않는다. candidate와 보고서만 만들고 새 session reviewer가 script hash와 스킬 본문을 확인한 뒤 승격한다.

## 오케스트레이션

```text
inventory
→ discover
→ check
→ analyze
→ propose
→ approval
→ stage
→ protected-asset approval
→ validate
→ promote
→ handoff
```

### 1. inventory

- `maintainer/upstreams/registry.json`
- `maintainer/upstreams/lock.json`
- `maintainer/upstreams/provenance/current-skills.json`
- `skills/**`
- `maintainer/upstreams/candidates/**`

현재 등록된 source, local skill, 관계 유형(`native`, `reference`, `adapted`, `vendored`)을 확인한다.

### 2. discover

`scripts/discover_upstreams.py`를 사용한다.

- 새 공식·유명 source 후보를 보고서로만 생성한다.
- 후보마다 provenance URL, 확인일, maintainer, 활성도, 라이선스, 보안 표면, 기능 적합성, 중복도를 기록한다.
- candidate 등록과 파일 반입은 승인 전 수행하지 않는다.

### 3. check

`scripts/check_upstreams.py`를 사용한다.

- 등록된 upstream의 latest stable release/tag/branch SHA를 확인한다.
- prerelease는 제외한다.
- GitHub 장애·rate limit이 발생해도 현재 pinned 상태를 손상하지 않는다.
- `--write-observed`를 명시한 경우에도 `observed`만 갱신한다.

### 4. analyze

관계 유형별 reference를 따른다.

- `references/reference-mode.md`
- `references/vendored-mode.md`
- `references/adapted-mode.md`

reference는 개념·권장사항 차이만 분석한다. vendored는 파일·hash·license diff를 분석한다. adapted는 upstream base와 local patch의 semantic mapping을 분석한다.

### 5. propose

`templates/upstream-review-report.md`와 `templates/asset-impact-report.md`로 보고서를 작성한다.

보고서에는 다음을 반드시 분리한다.

- 추가·내용 수정·보완 파일
- 삭제·이동·교체 파일
- scripts/hooks/MCP/network 권한 변화
- protected asset 영향
- Codex·Claude runtime 차이
- 채택·부분 채택·보류·거부 권장

### 6. approval

승인 ID를 기록한다.

- 일반 승인: update를 검토하고 staging을 허용
- asset-impact approval: protected asset 추가·수정·보완 허용
- destructive approval: 삭제·이동·교체 허용

승인 ID가 없으면 `promote`는 차단한다.

### 7. stage

`scripts/stage_upstream.py`를 사용한다.

- staging은 `maintainer/upstreams/staging/{candidate_id}/`에만 생성한다.
- canonical `skills/**`, plugin runtime, embedded lock은 변경하지 않는다.
- allowlist와 file-map을 검증한다.
- path traversal, symlink, submodule, binary/LFS 의심은 차단한다.

### 8. validate

- registry validator
- 관계 유형별 diff rule
- protected/destructive approval rule
- candidate fixture/eval
- 필요한 경우 dogfood hash 비교

### 9. promote

`scripts/promote_upstream.py`를 사용한다.

- 승인 ID, upstream SHA, source/runtime hash, validation 결과를 machine-readable promotion handoff로 기록한다.
- 검증 완료 전 embedded lock을 변경하지 않는다.
- plugin packaging이나 release는 수행하지 않고 `harness-plugin-maintainer`로 handoff한다.

### 10. rollback

`scripts/rollback_upstream.py`를 사용한다.

- promotion handoff의 이전 lock snapshot 또는 현재 lock state를 기준으로 rollback report를 만든다.
- 파괴적 명령을 자동 실행하지 않는다.

## 검증

`evals/run_evals.py`를 실행한다.

```bash
python maintainer/skills/skill-portfolio-maintainer/evals/run_evals.py
```

합격 조건:

- known upstream refresh와 new discovery가 다른 보고서·상태 전이를 사용한다.
- reference는 외부 파일 copy를 자동 제안하지 않는다.
- adapted는 vendored처럼 덮어쓰지 않는다.
- protected asset 승인 없는 추가·수정·보완은 차단한다.
- destructive 승인 없는 삭제·이동·교체는 차단한다.
- license/security/path 위험은 차단한다.
- self-update same-session promote는 차단한다.
