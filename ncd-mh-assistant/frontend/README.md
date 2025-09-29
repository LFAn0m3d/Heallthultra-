# NCD & Mental Health Assistant – Frontend

Expo React Native application that connects to the FastAPI backend to capture intake information, show triage results, and visualise trends (textual for MVP).

## Prerequisites
- Node.js 18+
- `npm` or `yarn`
- Expo CLI (installed via `npm install -g expo-cli`, optional when using `npx expo`)

## Setup & Run
```bash
cd frontend
npm install
export EXPO_PUBLIC_API_URL=http://<YOUR-IP>:8000
npm run start
```

Use the Expo dev tools to open the app on a simulator or physical device.

## Environment Variables
- `EXPO_PUBLIC_API_URL` – Base URL pointing at the running backend (defaults to `http://localhost:8000`).

## Screens
- **Home:** Navigation hub with warnings.
- **Intake:** Capture symptoms and request triage analysis.
- **Result:** Show triage level, rationale, and recommended actions.
- **Trends:** Query longitudinal metrics and display textual summaries.
