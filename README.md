# Crown Live Bus 🚌

Mobile-first real-time bus tracking for the Crown Taloja commuter network.

## v1
- React + TypeScript + Vite frontend
- Framer Motion animations
- Dark responsive interface
- Passenger and Driver modes
- Crown Taloja → Dombivli timetable (29 trips)
- Dombivli, Xperia Mall and Kharghar route/stops data
- Driver GPS start/stop controls
- Ready for FastAPI/PostgreSQL/WebSocket backend
- Vercel-friendly static build

## Run
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
```

## Live location architecture
Driver browser GPS → API/WebSocket → PostgreSQL/PostGIS → Passenger map.

For production, configure authentication, a real bus/fleet record, map tiles/routing and a FastAPI service via environment variables. Never commit credentials or API keys.
