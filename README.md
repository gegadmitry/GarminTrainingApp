# Garmin Training App

A starting point for vibecoding a Garmin-focused training application.

## Status

Early project setup. The application and development workflow will be added in future commits.

## Local activity browser

Start the API with `uvicorn garmin_training.api:app --reload`, then start the
frontend from `frontend/` with `npm install && npm run dev`. The browser reads
local activity data from `http://127.0.0.1:8000` by default; set `VITE_API_URL`
when the API runs elsewhere.
