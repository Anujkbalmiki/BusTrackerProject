# Crown Live Bus 🚌

Mobile-first real-time bus tracking for the Crown Taloja commuter network.

## What is implemented
- React + TypeScript + Vite
- Framer Motion UI transitions
- Dark responsive passenger + driver consoles
- OpenStreetMap + Leaflet live map
- Crown Taloja → Dombivli timetable with 29 departures from the supplied schedule
- Dombivli, Xperia Mall and Kharghar route selectors
- Driver GPS Start Trip / Stop Trip controls
- Live GPS polling on passenger screens every 5 seconds
- FastAPI serverless API under `/api`
- PostgreSQL persistence when `DATABASE_URL` is configured
- Development fallback store when no database is configured
- PostGIS schema for production spatial data
- Vercel rewrite configuration
- Demo access is open by default

## Run locally
```bash
npm install
npm run dev
```

API locally:
```bash
uvicorn api.index:app --reload
```

## Production architecture
```text
Driver phone GPS
      ↓
FastAPI /api/driver/location
      ↓
PostgreSQL + PostGIS
      ↓
/api/live polling (5 sec)
      ↓
Passenger Leaflet / OpenStreetMap map
```

## Production setup
1. Create a PostgreSQL database with PostGIS and run `sql/schema.sql`.
2. Add `DATABASE_URL` to the Vercel project environment.
3. Deploy the repository to Vercel.
4. Configure Google + phone authentication using the Firebase variables in `.env.example` and replace the demo sign-in handler in `src/main.tsx` with the Firebase Auth flow.
5. Replace the route stop list with verified latitude/longitude pairs before displaying stop pins or calculating exact stop ETAs. Do not use guessed coordinates in production.

## Important GPS behavior
The browser requests high-accuracy GPS only after the driver presses **Start Trip**. Updates are posted while the trip is active. **Stop Trip** calls the API and clears the browser geolocation watcher. Passenger live records are considered stale after two minutes on the persistent backend.

## Notes
The current serverless fallback is intentionally suitable for UI/demo testing only. Vercel function instances are ephemeral, so production live tracking requires `DATABASE_URL` (or another shared realtime store). A future WebSocket/SSE layer can reduce passenger polling, but the 5-second polling implementation is deliberately simple and reliable for v1.

Never commit credentials or API keys.
