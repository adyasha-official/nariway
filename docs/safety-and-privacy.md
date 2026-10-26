# Safety and privacy principles

## Safety principles
1. No route is guaranteed safe. Copy never says "safe" as a promise.
2. Missing data stays missing. Absence of reports is not evidence of safety (tested in `test_scoring.py`).
3. Every assessment shows its evidence, freshness, coverage and model version.
4. Risk and uncertainty are shown separately: "unknown" and "risky" are different.
5. The Fastest route still displays known hazards.
6. Sample or demo data is always labelled and kept separate from real data.
7. Emergency and live-tracking features are not presented as operational until tested end to end.

## Community reports: abuse controls (BUILT, see tests/test_platform.py)
- Category-based form; free text limited, no names or personal descriptions.
- Rate limits, duplicate detection, flag-and-review flow, expiry with half-life decay.
- Moderation guidelines covering bias against communities or neighbourhoods.

## Privacy (controls built; policy text still to write before pilot)
- Route comparison works without an account.
- Do not store searches or trips by default. If stored: defined retention, user-visible delete.
- Share tokens are unguessable, hashed at rest, expiring and revocable.
- Write the privacy policy against the DPDP Act, 2023.

## Third-party services
Public OSRM and Nominatim demo servers are not for production use. Plan to self-host a routing engine or use a provider whose terms allow the use, and budget for it.

## Status of safety-critical features (be honest in the UI)
- Journey Guardian is a **shared-link check-in**, not live tracking. NariWay does **not** send SMS/WhatsApp/push alerts for missed arrivals. The contact sees "Overdue" only when they open the link. Do not describe it otherwise until delivery is built and tested.
- There is **no SOS button**. 112 is shown as static information.
- Sample (demo) routes, indicators and reports are labelled "Sample data" everywhere they appear.
- Not yet done: privacy policy text (DPDP Act, 2023), Alembic migrations, PostGIS spatial queries, HTTPS/deploy config, real lighting/open-hours data audit, field validation on real routes.
