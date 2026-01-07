# PARS WMS (v1.8.1 ready)

FastAPI + SQLite 기반 WMS (PC / 모바일 / QR / 엑셀 업로드 / 라벨 / 달력 메모)

## 1) 로컬 실행
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

접속:
- 홈: http://localhost:8000/
- PC 메뉴: /page/inbound, /page/outbound, /page/move, /page/inventory, /page/history, /page/excel, /page/labels, /page/calendar
- 모바일: /m
- 로그인: /login

(편의용 리다이렉트: /inbound, /outbound, /move, /inventory, /history, /calendar 등도 동작)

## 2) 기본 관리자 계정
- ID: admin
- PW: admin123

배포 시에는 환경변수로 변경 권장:
- PARS_ADMIN_USER (기본 admin)
- PARS_ADMIN_PASS (기본 admin123)

## 3) 배포 (Render / Railway 공통)
### 권장 Start Command
Render의 **Custom Start Command**(또는 Railway Start Command)에 아래를 사용하세요.
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

> Dockerfile을 그대로 쓰는 방식이면(Start Command 비움) 컨테이너 CMD가 `$PORT`(없으면 8080)로 동작합니다.

## 4) DB
- SQLite 파일은 실행 시 자동 생성됩니다: `app/data/wms.db`
- GitHub에는 DB 파일을 커밋하지 않도록 `.gitignore`에 포함되어 있습니다.

## 5) 엑셀 업로드 컬럼 (입고/출고/이동 공통)
`창고 / 로케이션 / 브랜드 / 품번 / 품명 / LOT / 규격 / 수량 / 비고`

---
✅ 이 ZIP은 __pycache__ / *.pyc / *.db 제거, 달력(월 메모) 기능 추가, 기본 관리자 비밀번호(admin123) 반영 버전입니다.
