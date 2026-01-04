# QR 관련 전체 교체 가이드

아래 파일들을 ZIP 안의 동일 경로로 **그대로 교체**하면 됩니다.

## 1) QR 표준/파서
- `app/utils/qr_format.py`

## 2) 모바일 QR 스캔/분기
- `app/pages/mobile_qr.py`
- `app/templates/m/qr_scan.html` (문구 업데이트)

## 3) 모바일 QR 이동(신규)
- `app/pages/mobile_move.py` (신규)
- `app/templates/m/move_home.html` (신규)
- `app/templates/m/move_from.html` (신규)
- `app/templates/m/move_select.html` (신규)
- `app/templates/m/move_to.html` (신규)
- `app/templates/m/move_done.html` (신규)
- `app/templates/m/home.html` (메뉴에 'QR 이동' 링크 추가)

## 4) 라우터 등록
- `app/main.py` (mobile_move_router include 추가)

## 5) 문서/예시
- `docs/QR_SPEC_v1.txt`, `docs/QR_SPEC_v1.pdf`
- `docs/QR_MOVE_ONEPAGER.txt`, `docs/QR_MOVE_ONEPAGER.pdf`
- `docs/qr_examples/*.png`

## 테스트 체크리스트
1. 서버 실행 후 `/m` 접속 → `QR 이동` 메뉴가 보이는지
2. `/m/qr`에서 로케이션 QR 스캔 → 로케이션 재고 페이지로 이동되는지
3. `/m/qr`에서 품목 QR 스캔 → 품목 상세 페이지로 이동되는지
4. `/m/move` 흐름
   - 출발 로케이션 스캔
   - 품목 선택
   - 도착 로케이션 스캔 + 수량 입력
   - 이동 완료 후 `/page/history`에서 이력 확인
