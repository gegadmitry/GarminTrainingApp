# Local API

The FastAPI application is intended for local use only. Start it on loopback:

```sh
uvicorn garmin_training.api:app --host 127.0.0.1 --port 8000
```

The default database is `data/training.sqlite3`; set
`GARMIN_DATABASE_PATH` to use another local path. The API exposes typed
endpoints for health, sync status, and filtered activities. CORS allows only
the local frontend origins `127.0.0.1:5173` and `localhost:5173`.