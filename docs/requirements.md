# Requirements

## Users
Women travelling in an Indian city, often at night, often on a phone with a weak connection.

## MVP scope
Modules A (navigation) and B (safety intelligence) for **one pilot city**, as a mobile-first web app.

## Functional goals
1. Generate multiple viable routes between origin and destination.
2. Rank them for Safety First, Balanced and Fastest preferences.
3. Show evidence, source, freshness and coverage for each assessment.
4. Accept moderated community reports (after the safety engine).
5. Opt-in journey sharing (after privacy review).

## Deliberate changes from the first brief
| Brief | Change | Why |
|---|---|---|
| "One tap SOS" tile | Replaced with **Nearby Help** and a static 112 notice | A silent SOS failure during a real emergency is worse than no button |
| "Share your live location" | **Opt-in, time-limited, revocable** trip sharing, built later | Live tracking needs privacy and reliability work first |
| "The safest route" | "More verified safety information" | Avoids implying a guarantee |
| "Highest safety" / "Lower safety" map labels | "Most evidence" / "Shows hazards" | Labels must describe evidence, not promise outcomes |
| "in every city, at any time" | Pilot city only, limits disclosed | Coverage is genuinely limited |
| "Recommended" on Balanced | "Default" | We should not steer the user to a choice |

## Non-functional
- Accessibility: contrast checks on lavender backgrounds, keyboard operable, labelled controls.
- Privacy: no login required for route comparison; defined retention before any trip storage; DPDP Act, 2023 review.
- Reliability: graceful handling of denied location, offline, routing provider failure.
