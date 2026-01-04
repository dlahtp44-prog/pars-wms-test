# PARS WMS v1.6-stable

## Start (local)
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Deploy (Railway/Render)
Start Command (변경 불필요):
`uvicorn app.main:app --host 0.0.0.0 --port 8080`

DB는 최초 실행 시 자동 생성됩니다.
