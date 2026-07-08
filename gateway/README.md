# Gateway package

FastAPI app: `uvicorn app.main:app --host 0.0.0.0 --port 8080`

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

See the [repo README](../README.md) for env vars and deployment.
