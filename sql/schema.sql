create extension if not exists postgis;
create table if not exists routes(id text primary key,name text not null,direction text not null,active boolean default true);
create table if not exists stops(id bigserial primary key,route_id text references routes(id),name text not null,sequence_no int not null,lat double precision,lng double precision,location geography(point,4326));
create table if not exists buses(id text primary key,fleet_code text unique not null,route_id text references routes(id),driver_name text,status text default 'idle',last_seen_at timestamptz);
create table if not exists live_locations(bus_id text primary key references buses(id),location geography(point,4326) not null,lat double precision not null,lng double precision not null,speed_kmh double precision default 0,heading double precision default 0,accuracy_m double precision,is_tracking boolean default false,updated_at timestamptz default now());
create index if not exists live_locations_gix on live_locations using gist(location);
create table if not exists schedules(id bigserial primary key,route_id text references routes(id),origin_time text not null,destination_time text not null,active boolean default true);
insert into routes(id,name,direction) values ('ct-d','Crown Taloja → Dombivli','outbound'),('ct-x','Crown Taloja → Xperia Mall','outbound'),('ct-k','Crown Taloja → Kharghar','outbound') on conflict(id) do nothing;
insert into buses(id,fleet_code,route_id,status) values ('CROWN-01','CROWN-01','ct-d','idle') on conflict(id) do nothing;
