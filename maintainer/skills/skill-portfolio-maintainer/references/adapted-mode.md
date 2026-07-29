# Adapted Mode

외부 source의 핵심 구조·문구·아이디어를 local 하네스에 맞게 번역, 축약, 재구성, 재작성한 관계다.

## 분석 대상

- accepted upstream base tag/SHA
- local adaptation patch
- semantic mapping
- local-only 보호 규칙
- license/notice preservation
- behavior fixture drift

## 금지

- upstream 전체를 vendored처럼 덮어쓰기
- local patch 충돌 자동 보정
- protected references/scripts/templates 삭제
- platform-specific runtime을 다른 platform에 그대로 주입

## 결과

adapted source는 upstream base와 local patch를 분리해 보고한다. promote 시에는 source hash, runtime hash, validation 결과, 승인 ID를 promotion handoff에 기록한다.
