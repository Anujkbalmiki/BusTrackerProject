from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
import os

app = FastAPI(title='Crown Live Bus API', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

TIMETABLE = [
('06:00 AM','06:45 AM'),('06:30 AM','07:15 AM'),('07:00 AM','07:45 AM'),('07:30 AM','08:15 AM'),('08:00 AM','08:45 AM'),('08:30 AM','09:15 AM'),('09:00 AM','09:45 AM'),('09:30 AM','10:15 AM'),('10:00 AM','10:45 AM'),('10:30 AM','11:15 AM'),('11:00 AM','11:45 AM'),('11:30 AM','12:15 PM'),('12:30 PM','01:15 PM'),('01:00 PM','01:45 PM'),('02:30 PM','03:15 PM'),('03:15 PM','04:00 PM'),('04:00 PM','04:45 PM'),('04:45 PM','05:30 PM'),('05:15 PM','06:00 PM'),('05:45 PM','06:30 PM'),('06:15 PM','07:00 PM'),('06:45 PM','07:30 PM'),('07:15 PM','08:00 PM'),('07:45 PM','08:30 PM'),('08:15 PM','09:00 PM'),('08:45 PM','09:30 PM'),('09:15 PM','10:00 PM'),('09:45 PM','10:30 PM'),('10:15 PM','11:00 PM')]
ROUTES = {
'dombivli': {'id':'ct-d','name':'Crown Taloja → Dombivli','stops':['Crown Taloja','Katai Naka','Runwal Gardens Gate','D-Mart Road','AIMS Hospital Road','Pendharkar College','Dombivli Station']},
'xperia': {'id':'ct-x','name':'Crown Taloja → Xperia Mall','stops':['Crown Taloja','Katai Naka','Palava Gate','Xperia Mall Road']},
'kharghar': {'id':'ct-k','name':'Crown Taloja → Kharghar','stops':['Crown Taloja','Taloja MIDC','Lodha Industrial','Pisarve Ground','Taloja Phase-1','Sector 36','Kharghar Station']}
}
# Demo state is intentionally useful for preview/development. For production, set DATABASE_URL
# and move the live-location store to Postgres/PostGIS (see sql/schema.sql).
live_buses = {}

class Location(BaseModel):
    bus_id: str = Field(min_length=1)
    route_id: str = 'ct-d'
    driver_name: str = 'Demo Driver'
    lat: float
    lng: float
    speed_kmh: float = 0
    heading: float = 0
    accuracy_m: Optional[float] = None
    tracking: bool = True

class TripStart(BaseModel):
    bus_id: str = 'CROWN-01'
    route_id: str = 'ct-d'
    driver_name: str = 'Driver'

@app.get('/api/health')
def health():
    return {'ok': True, 'service': 'crown-live-bus', 'time': datetime.now(timezone.utc).isoformat()}

@app.get('/api/routes')
def routes():
    return list(ROUTES.values())

@app.get('/api/schedule')
def schedule(route: str = 'ct-d'):
    return [{'id': i+1, 'origin_time': a, 'destination_time': b, 'route': route} for i,(a,b) in enumerate(TIMETABLE)]

@app.get('/api/live')
def live(route: str = 'ct-d'):
    return [b for b in live_buses.values() if b['route_id'] == route and b['is_tracking']]

@app.post('/api/driver/start')
def start_trip(payload: TripStart):
    live_buses.setdefault(payload.bus_id, {
        'id': payload.bus_id, 'fleet_code': payload.bus_id, 'route_id': payload.route_id,
        'driver_name': payload.driver_name, 'status': 'active', 'is_tracking': True,
        'lat': 19.0760, 'lng': 73.1300, 'speed_kmh': 0, 'heading': 0, 'accuracy_m': None,
        'updated_at': datetime.now(timezone.utc).isoformat()
    })
    live_buses[payload.bus_id].update(driver_name=payload.driver_name, route_id=payload.route_id, status='active', is_tracking=True)
    return {'ok': True, 'trip_id': f"trip-{payload.bus_id}-{int(datetime.now().timestamp())}"}

@app.post('/api/driver/location')
def location(payload: Location):
    if not payload.tracking:
        return stop_trip({'bus_id': payload.bus_id})
    if payload.bus_id not in live_buses:
        live_buses[payload.bus_id] = {'id':payload.bus_id,'fleet_code':payload.bus_id}
    live_buses[payload.bus_id].update({
        'route_id':payload.route_id,'driver_name':payload.driver_name,'status':'active','is_tracking':True,
        'lat':payload.lat,'lng':payload.lng,'speed_kmh':max(0,payload.speed_kmh),'heading':payload.heading,
        'accuracy_m':payload.accuracy_m,'updated_at':datetime.now(timezone.utc).isoformat()
    })
    return {'ok': True}

@app.post('/api/driver/stop')
def stop_trip(payload: dict):
    bus_id = payload.get('bus_id')
    if not bus_id: raise HTTPException(400, 'bus_id is required')
    if bus_id in live_buses:
        live_buses[bus_id]['status'] = 'idle'; live_buses[bus_id]['is_tracking'] = False
        live_buses[bus_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
    return {'ok': True}
