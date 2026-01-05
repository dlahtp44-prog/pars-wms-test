# PARS WMS v1.6-final (안정판)

## 포함 기능
- PC: 입고/출고/이동/재고조회/이력조회(년/월/일 필터, 엑셀 다운로드)
- 엑셀 업/다운로드 센터: 입고/출고/이동 업로드, 재고/이력 다운로드
- 달력: **단순 메모(저장/수정/삭제)**
- 모바일: /m, /m/qr (재고조회 / 이동)

## 로컬 실행
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker
```bash
docker build -t pars-wms .
docker run -p 8080:8080 pars-wms
```
