# Real routes and map data

NariWay shows labelled demo routes until a routing server is configured. This page gets you to real routes and real map evidence for the pilot city (Rourkela by default). Do the steps in order.

Two separate things are involved:

- **Routes** come from a routing server (OSRM).
- **Evidence** (lighting, footpaths, road type, open places) comes from a map-data file you download once. If a tag is missing from the map, NariWay shows **unknown**, never "safe".

## 1. Download the map data and read the audit (do this first)

From the project folder, with the backend virtual environment active:

```bash
make osm            # or: cd backend && python -m app.osm_fetch
```

This takes a minute or two and needs internet. It writes:

- `backend/data/osm_rourkela.json`: used by the scorer and by place search (not committed to Git)
- `docs/data-audit-rourkela.md`: how much of the map is usable. **Read this before trusting any score.**

The audit says how much of the road network has `lit` (lighting) and footpath tags, and how many places have opening hours NariWay can read. In many Indian cities these are sparse. That is expected, and the app handles it by showing unknown.

Default radius is 7 km around the pilot centre, enough to cover NIT Rourkela. Use `--radius 4000` if Overpass is slow or busy (that radius reaches the city centre and station but not the NIT campus). The script retries busy servers and falls back to other public Overpass servers automatically. Pass `--endpoint URL` to use one specific server only. These are fair-use public services, so do not run it repeatedly.

Once the file exists, the search box on the Navigate page searches the named places and streets in it.

## 2. Get routes

OSRM runs one profile per server, so walking, cycling and driving use separate URLs. Create `backend/.env` (it is ignored by Git) with the ones you want.

### Option A: public servers (development only, no Docker needed)
OpenStreetMap Germany runs public OSRM servers. Put this in `backend/.env`:

```
ROUTING_URL_WALK=https://routing.openstreetmap.de/routed-foot
ROUTING_URL_BIKE=https://routing.openstreetmap.de/routed-bike
ROUTING_URL_CAB=https://routing.openstreetmap.de/routed-car
```

Restart the backend. These are fair-use servers with no guarantees. They are not for production, and one "Compare routes" click makes up to three requests. Check their current usage policy and that the URLs still work. **These were not reachable from the environment where this code was written, so this path has not been tested end to end.** If a request fails you will see "Routing service is unavailable", and the first thing to try is opening one URL in a browser, such as `https://routing.openstreetmap.de/routed-foot/route/v1/driving/84.9006,22.2536;84.864,22.229`.

### Option B: self-host (recommended for the pilot, needs Docker)
Get an OSM extract that covers your city (a regional extract from geofabrik.de) and clip it:

```bash
mkdir -p osrm
osmium extract -b 84.75,22.15,84.98,22.35 region.osm.pbf -o osrm/rourkela.osm.pbf   # brew install osmium-tool
```

OSRM serves one profile per dataset, so build a dataset per mode:

```bash
IMG=ghcr.io/project-osrm/osrm-backend
for p in foot bicycle car; do
  cp osrm/rourkela.osm.pbf osrm/rourkela-$p.osm.pbf
  docker run --rm -v "$PWD/osrm:/data" $IMG osrm-extract   -p /opt/$p.lua /data/rourkela-$p.osm.pbf
  docker run --rm -v "$PWD/osrm:/data" $IMG osrm-partition /data/rourkela-$p.osrm
  docker run --rm -v "$PWD/osrm:/data" $IMG osrm-customize /data/rourkela-$p.osrm
done

docker run -d -p 5001:5000 -v "$PWD/osrm:/data" $IMG osrm-routed --algorithm mld /data/rourkela-foot.osrm
docker run -d -p 5002:5000 -v "$PWD/osrm:/data" $IMG osrm-routed --algorithm mld /data/rourkela-bicycle.osrm
docker run -d -p 5003:5000 -v "$PWD/osrm:/data" $IMG osrm-routed --algorithm mld /data/rourkela-car.osrm
```

Then set `ROUTING_URL_WALK=http://localhost:5001`, `ROUTING_URL_BIKE=http://localhost:5002`, `ROUTING_URL_CAB=http://localhost:5003`. Command details change between OSRM versions, so check the OSRM backend documentation if a step fails. These commands follow the documented workflow and have not been run in the environment where this was written.

If you only set the walking URL, the Bike and Cab options fall back to labelled demo routes.

## 3. Check the result

Open `/navigate`, search for two places, and click **Compare routes**. You should see:

- The "Sample data" banner is **gone**.
- A note under the route cards saying the map data came from OpenStreetMap, with its date.
- Routes that follow real roads.

If routes appear but most indicators say Unknown, the map file is missing or your area has few tags. That is the audit telling you something true, not a bug. When almost nothing is mapped, a note under the route cards says so.

Common messages:

| Message | Meaning |
|---|---|
| "No route found. Both points need to be near a road or path inside the covered area." | A point is off the road network, or outside the area you loaded |
| "Routing service is unavailable" | The routing URL did not answer: check it, or your internet |
| Banner "No local map data found" | Run `make osm` |

## How alternatives are generated
OSRM often returns one route, or near-copies. NariWay also requests routes forced through points on either side of the midpoint, drops near-duplicates (more than 90% overlap) and drops anything slower than 1.6 times the fastest. Test this on real trips and tune `VIA_OFFSETS` in `backend/app/services/routing/osrm.py`.

## What the evidence means
- **Lighting**: the share of the route on roads mapped lit or unlit. Untagged roads are unknown.
- **Footpaths**: from `sidewalk` tags on roads. A way that is itself a footpath or trail does not count as evidence, because it may be isolated.
- **Road type**: a heuristic. Busy main roads count as more people around, paths and tracks as more isolated. It is a weak proxy, so validate it with field walks.
- **Open places**: shops and services whose mapped opening hours say they are open at the time of travel, within 60 m.

None of these is a measurement of danger. The tuning values are in `backend/app/services/osm/evidence.py`.
