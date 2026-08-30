from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
import os

try:
    import psycopg
except ImportError:
    psycopg = None

app=FastAPI(title='Crown Live Bus API',version='1.1.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=False,allow_methods=['*'],allow_headers=['*'])
TIMETABLE=[('06:00 AM','06:45 AM'),('06:30 AM','07:15 AM'),('07:00 AM','07:45 AM'),('07:30 AM','08:15 AM'),('08:00 AM','08:45 AM'),('08:30 AM','09:15 AM'),('09:00 AM','09:45 AM'),('09:30 AM','10:15 AM'),('10:00 AM','10:45 AM'),('10:30 AM','11:15 AM'),('11:00 AM','11:45 AM'),('11:30 AM','12:15 PM'),('12:30 PM','01:15 PM'),('01:00 PM','01:45 PM'),('02:30 PM','03:15 PM'),('03:15 PM','04:00 PM'),('04:00 PM','04:45 PM'),('04:45 PM','05:30 PM'),('05:15 PM','06:00 PM'),('05:45 PM','06:30 PM'),('06:15 PM','07:00 PM'),('06:45 PM','07:30 PM'),('07:15 PM','08:00 PM'),('07:45 PM','08:30 PM'),('08:15 PM','09:00 PM'),('08:45 PM','09:30 PM'),('09:15 PM','10:00 PM'),('09:45 PM','10:30 PM'),('10:15 PM','11:00 PM')]
ROUTES={'ct-d':{'id':'ct-d','name':'Crown Taloja → Dombivli','stops':['Crown Taloja','Katai Naka','Runwal Gardens Gate','D-Mart Road','AIMS Hospital Road','Pendharkar College','Dombivli Station']},'ct-x':{'id':'ct-x','name':'Crown Taloja → Xperia Mall','stops':['Crown Taloja','Katai Naka','Palava Gate','Xperia Mall Road']},'ct-k':{'id':'ct-k','name':'Crown Taloja → Kharghar','stops':['Crown Taloja','Taloja MIDC','Lodha Industrial','Pisarve Ground','Taloja Phase-1','Sector 36','Kharghar Station']}}
live_buses={}
def now(): return datetime.now(timezone.utc).isoformat()
def db_enabled(): return bool(os.getenv('DATABASE_URL')) and psycopg is not None
def conn(): return psycopg.connect(os.environ['DATABASE_URL'])
def ensure_db():
    if not db_enabled(): return
    with conn() as c:
        c.execute("create table if not exists buses(id text primary key,fleet_code text unique not null,route_id text,driver_name text,status text default 'idle',last_seen_at timestamptz)")
        c.execute("create table if not exists live_locations(bus_id text primary key references buses(id) on delete cascade,lat double precision not null,lng double precision not null,speed_kmh double precision default 0,heading double precision default 0,accuracy_m double precision,is_tracking boolean default false,updated_at timestamptz default now())")
        c.execute("insert into buses(id,fleet_code,route_id,status) values('CROWN-01','CROWN-01','ct-d','idle') on conflict(id) do nothing")
def read_live(route):
    if not db_enabled(): return [b for b in live_buses.values() if b.get('route_id')==route and b.get('is_tracking')]
    ensure_db()
    with conn() as c: rows=c.execute("select b.id,b.fleet_code,b.route_id,b.driver_name,b.status,l.is_tracking,l.lat,l.lng,l.speed_kmh,l.heading,l.accuracy_m,l.updated_at from buses b join live_locations l on l.bus_id=b.id where b.route_id=%s and l.is_tracking=true and l.updated_at > now()-interval '2 minutes'",(route,)).fetchall()
    keys=['id','fleet_code','route_id','driver_name','status','is_tracking','lat','lng','speed_kmh','heading','accuracy_m','updated_at']
    return [dict(zip(keys,r)) for r in rows]
class Location(BaseModel):
    bus_id:str=Field(min_length=1);route_id:str='ct-d';driver_name:str='Driver';lat:float;lng:float;speed_kmh:float=0;heading:float=0;accuracy_m:Optional[float]=None;tracking:bool=True
class TripStart(BaseModel): bus_id:str='CROWN-01';route_id:str='ct-d';driver_name:str='Driver'
class StopPayload(BaseModel): bus_id:str
@app.get('/api/health')
def health(): return {'ok':True,'service':'crown-live-bus','persistent_store':db_enabled(),'time':now()}
@app.get('/api/routes')
def routes(): return list(ROUTES.values())
@app.get('/api/schedule')
def schedule(route:str='ct-d'): return [{'id':i+1,'origin_time':a,'destination_time':b,'route':route} for i,(a,b) in enumerate(TIMETABLE)]
@app.get('/api/live')
def live(route:str='ct-d'): return read_live(route)
@app.post('/api/driver/start')
def start_trip(p:TripStart):
    if db_enabled():
        ensure_db()
        with conn() as c:
            c.execute("insert into buses(id,fleet_code,route_id,driver_name,status,last_seen_at) values(%s,%s,%s,%s,'active',now()) on conflict(id) do update set route_id=excluded.route_id,driver_name=excluded.driver_name,status='active',last_seen_at=now()",(p.bus_id,p.bus_id,p.route_id,p.driver_name))
            c.execute("insert into live_locations(bus_id,lat,lng,is_tracking,updated_at) values(%s,19.0760,73.1300,true,now()) on conflict(bus_id) do update set is_tracking=true,updated_at=now()",(p.bus_id,))
    else: live_buses[p.bus_id]={'id':p.bus_id,'fleet_code':p.bus_id,'route_id':p.route_id,'driver_name':p.driver_name,'status':'active','is_tracking':True,'lat':19.0760,'lng':73.1300,'speed_kmh':0,'heading':0,'accuracy_m':None,'updated_at':now()}
    return {'ok':True,'trip_id':f"trip-{p.bus_id}-{int(datetime.now().timestamp())}",'persistent_store':db_enabled()}
@app.post('/api/driver/location')
def location(p:Location):
    if not p.tracking: return stop_trip(StopPayload(bus_id=p.bus_id))
    if db_enabled():
        ensure_db()
        with conn() as c:
            c.execute("update buses set route_id=%s,driver_name=%s,status='active',last_seen_at=now() where id=%s",(p.route_id,p.driver_name,p.bus_id))
            c.execute("insert into live_locations(bus_id,lat,lng,speed_kmh,heading,accuracy_m,is_tracking,updated_at) values(%s,%s,%s,%s,%s,%s,true,now()) on conflict(bus_id) do update set lat=excluded.lat,lng=excluded.lng,speed_kmh=excluded.speed_kmh,heading=excluded.heading,accuracy_m=excluded.accuracy_m,is_tracking=true,updated_at=now()",(p.bus_id,p.lat,p.lng,max(0,p.speed_kmh),p.heading,p.accuracy_m))
    else: live_buses[p.bus_id]={'id':p.bus_id,'fleet_code':p.bus_id,'route_id':p.route_id,'driver_name':p.driver_name,'status':'active','is_tracking':True,'lat':p.lat,'lng':p.lng,'speed_kmh':max(0,p.speed_kmh),'heading':p.heading,'accuracy_m':p.accuracy_m,'updated_at':now()}
    return {'ok':True}
@app.post('/api/driver/stop')
def stop_trip(p:StopPayload):
    if db_enabled():
        ensure_db()
        with conn() as c: c.execute("update buses set status='idle',last_seen_at=now() where id=%s",(p.bus_id,)); c.execute("update live_locations set is_tracking=false,updated_at=now() where bus_id=%s",(p.bus_id,))
    elif p.bus_id in live_buses: live_buses[p.bus_id].update(status='idle',is_tracking=False,updated_at=now())
    return {'ok':True}
