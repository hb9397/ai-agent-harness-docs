# Vendored Mode

외부 파일을 거의 그대로 저장소에 보관하는 관계다.

## 분석 대상

- file hash diff
- mode/permission diff
- license and notice diff
- scripts/hooks/MCP/network permission changes
- symlink, submodule, path traversal, binary/LFS
- deleted, moved, replaced files

## 승인 게이트

- 일반 변경: general approval 필요
- protected asset 추가·수정·보완: asset-impact approval 필요
- 삭제·이동·교체: destructive approval 필요
- license 변경 또는 불명확한 권리: 차단

## 결과

vendored 파일은 file-map과 hash를 남긴 뒤 staging에서 검증한다. 검증 실패 시 canonical source와 embedded lock을 변경하지 않는다.
