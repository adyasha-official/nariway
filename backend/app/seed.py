"""Seed CLEARLY-LABELLED sample reports (is_demo=True) so the map has something to show.

    python -m app.seed         # add sample reports
    python -m app.seed --clear # remove them

Sample reports are never real observations and the UI marks them as sample data.
"""

import sys
from datetime import timedelta

from sqlalchemy import delete

from app.db import Base, SessionLocal, engine, utcnow
from app.models import SafetyReport
import app.models as _m  # noqa: F401

SAMPLES = [
    ("poor_lighting", "Sample: street lamps not working on this stretch.", 22.2455, 84.8795),
    ("isolated", "Sample: long quiet stretch with few people after dark.", 22.2410, 84.8690),
    ("unsafe_crossing", "Sample: busy crossing without a signal.", 22.2330, 84.8660),
    ("obstruction", "Sample: footpath blocked by construction material.", 22.2500, 84.8900),
]


def main() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.execute(delete(SafetyReport).where(SafetyReport.is_demo))
        if "--clear" not in sys.argv:
            now = utcnow()
            for i, (cat, text, lat, lng) in enumerate(SAMPLES):
                db.add(SafetyReport(category=cat, description=text, lat=lat, lng=lng, status="approved", is_demo=True,
                                    occurred_at=now - timedelta(days=3 + i * 4), expires_at=now + timedelta(days=60)))
        db.commit()
    print("cleared sample reports" if "--clear" in sys.argv else f"seeded {len(SAMPLES)} sample reports")


if __name__ == "__main__":
    main()
