# Reference Mode

외부 source를 참고만 하는 관계다. upstream 파일, 번역문, template, script, asset을 저장소에 반입하지 않는다.

## 분석 대상

- 공식 권장사항 변화
- workflow·용어·검증 관점 변화
- local skill과 충돌하는 정책 변화
- deprecation 또는 platform capability 변화

## 금지

- upstream 파일 copy 제안 자동 생성
- 외부 문구 번역·요약을 local source로 바로 반영
- protected asset 변경 자동 제안

## 결과

- report에는 개념 차이와 채택 후보만 기록한다.
- local source 변경은 별도 adapted/vendored 재분류 승인 뒤 수행한다.
