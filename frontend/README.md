# Rent-a-Thing — Simple Frontend

Minimal single-page frontend (vanilla JS, no build). Uses the Rent-a-Thing FastAPI backend.

## Run with the API (recommended)

1. Start the backend (e.g. `uvicorn app.main:app --reload` from project root).
2. Open **http://localhost:8000/app/** in the browser.

The app is served by FastAPI from the `frontend/` folder, so API calls use the same origin (no CORS).

## Run standalone (different port)

If you serve the frontend from another port (e.g. `python -m http.server 3000` in `frontend/`):

- Open **http://localhost:3000**
- Set the API base: in the browser console run `window.__API_BASE__ = 'http://localhost:8000'` before navigating, or edit `app.js` and set `API_BASE` to `'http://localhost:8000'`.
- Ensure the backend has `CORS_ORIGINS=*` or includes your frontend origin.

## Features

- **Browse** — list items from `GET /items`
- **Log in / Register** — JWT stored in `localStorage`
- **Item detail** — view one item; **Request booking** (dates + notes) when logged in as a renter
- **My bookings** — list your bookings from `GET /bookings/me/renter`
