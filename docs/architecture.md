# Architecture

```
React + TypeScript (Vite, Tailwind, Leaflet)
        |
FastAPI  -- auth, validation, rate limits
   |-- routing service (OSRM / Valhalla / GraphHopper, self-hosted)
   |-- safety engine   (rules-based scoring, model version recorded)
   |-- PostgreSQL + PostGIS (reports, evidence, places, trips)
   `-- notifications   (later, opt-in only)
```

## Scoring model v0 (`backend/app/services/safety/scoring.py`)
`C(r) = w_t*T + w_d*D + w_r*R + w_u*U`, lower is better.
- T, D normalised against the best candidate.
- R from evidence; unknown risk is mid-scale, never zero.
- U = 1 - evidence coverage, so silence is penalised.

## Planned improvements
- Time-of-day dependent evidence (open shops matter at 9 pm, not 2 pm).
- Report decay with category half-lives.
- Alternative-route diversity via penalty or via-point methods; measure similarity early.

## Repository layout
See README. Frontend and backend live in one repository for now.
