# API (v1) — base path `/api/v1`

| Method & path | Auth | Purpose |
|---|---|---|
| GET `/places/search?q=` | – | Place search (demo gazetteer or Nominatim) |
| POST `/routes/alternatives` | – | Candidate routes + assessment. Includes approved reports near each route |
| POST `/routes/assess` | – | Rank supplied candidates |
| POST `/auth/register`, `/auth/login` | – | Rate-limited (10/min/IP). bcrypt + JWT |
| GET / DELETE `/auth/me` | user | Profile / erase account (trips, contacts, shares deleted; reports anonymised) |
| GET `/safety/categories` | – | Report categories |
| POST `/safety/reports` | user | Submit (pending). PII filter, duplicate check, 5/day, time window 30 days |
| GET `/safety/reports?min_lat&max_lat&min_lng&max_lng` | – | Approved, unexpired reports only. No reporter info |
| GET `/safety/reports/mine` | user | Own reports with status |
| POST `/safety/reports/{id}/flag` | user | One flag per user; 3 flags hide the report pending review |
| GET `/admin/reports?status=`, POST `/admin/reports/{id}/moderate`, GET `/admin/stats`, `/admin/audit` | admin | Moderation queue and audit trail |
| GET/POST/DELETE `/contacts` | user | Trusted contacts (consent required, max 10) |
| POST/GET `/trips`, POST `/trips/{id}/check-in`, `/trips/{id}/end` | user | Journeys (ETA ≤ 24 h, ≤ 3 active). Ending revokes links and clears location |
| POST `/trips/{id}/share`, GET `/trips/{id}/shares`, DELETE `/trips/{id}/shares/{sid}` | user | Share links: 256-bit token, stored as SHA-256, shown once, expiring, revocable |
| GET `/shared/{token}` | – | Contact view: first name, destination, state, ETA, last check-in. Uniform 404 for invalid/revoked/expired |
