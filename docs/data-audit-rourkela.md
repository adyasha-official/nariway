# Data audit: Rourkela

Fetched 2026-11-01 from OpenStreetMap, 7000 m around the pilot centre. OpenStreetMap is map data, not a safety database.

## Roads
- 4160 ways, 1016.6 km
- `lit` tag known: **0.0%** (lit: 0.0%, unlit: 0.0%)
- Sidewalk/footpath known: **0.0%**

| Road class | km | lighting known |
|---|---|---|
| residential | 615.0 | 0.0% |
| tertiary | 125.1 | 0.0% |
| service | 105.2 | 0.0% |
| unclassified | 70.8 | 0.0% |
| trunk | 52.4 | 0.0% |
| primary | 34.0 | 0.0% |
| footway | 6.6 | 0.0% |
| track | 4.8 | 0.0% |
| secondary | 1.7 | 0.0% |
| path | 0.6 | 0.0% |

## Places
- 107 mapped places, 88.8% named
- 2 with opening hours (1.9%); 100.0% of those can be read by NariWay
- By kind: hospital: 36, clinic: 29, restaurant: 8, fast_food: 8, shop: 5, bank: 5, marketplace: 4, station: 2, police: 2, cafe: 2, bus_station: 2, fuel: 2

## What this means
- Lighting is known for only 0.0% of road length. Lighting evidence will usually be UNKNOWN. Do not present lighting as a strong signal. Consider a mapping walk or mapathon to add `lit` tags.
- Footpath information covers 0.0% of roads: treat as mostly unknown.
- Few places have mapped opening hours, so 'open places nearby' will rarely be known. Do not use it to claim an area is busy.
- Road type is almost always available, but it is a weak proxy. Validate it with field walks before relying on it.
