"""Local OpenStreetMap extract with a simple grid index for nearest-way / nearby-place lookups."""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from math import cos, radians
from pathlib import Path

from app.schemas.routes import LatLng
from app.services.safety.geometry import haversine_m, point_segment_distance_m

CELL_DEG = 0.0009  # about 100 m


def _cell(lat: float, lng: float) -> tuple[int, int]:
    return int(lat / CELL_DEG), int(lng / CELL_DEG)


@dataclass
class OsmStore:
    fetched_at: str
    ways: list[dict]
    pois: list[dict]
    _seg_index: dict = field(default_factory=lambda: defaultdict(list), repr=False)
    _poi_index: dict = field(default_factory=lambda: defaultdict(list), repr=False)
    _names: list | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for wi, w in enumerate(self.ways):
            g = w["geom"]
            for si in range(len(g) - 1):
                (a, b) = g[si], g[si + 1]
                # register the segment in every cell its bounding box touches
                c0, c1 = _cell(min(a[0], b[0]), min(a[1], b[1])), _cell(max(a[0], b[0]), max(a[1], b[1]))
                for i in range(c0[0], c1[0] + 1):
                    for j in range(c0[1], c1[1] + 1):
                        self._seg_index[(i, j)].append((wi, si))
        for pi, p in enumerate(self.pois):
            self._poi_index[_cell(p["lat"], p["lng"])].append(pi)

    @classmethod
    def load(cls, path: str | Path) -> "OsmStore | None":
        p = Path(path)
        if not p.exists():
            return None
        d = json.loads(p.read_text())
        return cls(fetched_at=d.get("fetched_at", "unknown"), ways=d["ways"], pois=d["pois"])

    def _name_index(self) -> list[tuple[str, str, float, float]]:
        """(lowercase name, display name, lat, lng): named places first, then street names."""
        if self._names is None:
            seen: set[str] = set()
            rows = []
            for p in self.pois:
                if p.get("name") and p["name"].lower() not in seen:
                    seen.add(p["name"].lower())
                    rows.append((p["name"].lower(), p["name"], p["lat"], p["lng"]))
            for w in self.ways:
                if w.get("name") and w["name"].lower() not in seen and w.get("geom"):
                    seen.add(w["name"].lower())
                    mid = w["geom"][len(w["geom"]) // 2]
                    rows.append((w["name"].lower(), w["name"], mid[0], mid[1]))
            self._names = rows
        return self._names

    def search(self, q: str, limit: int = 6) -> list[dict]:
        """Name search over places and streets in the extract. Prefix matches rank above word-start above substring."""
        q = q.strip().lower()
        if len(q) < 2:
            return []
        hits = []
        for low, name, lat, lng in self._name_index():
            if low.startswith(q):
                rank = 0
            elif any(wd.startswith(q) for wd in low.replace("-", " ").replace(",", " ").split()):
                rank = 1
            elif q in low:
                rank = 2
            else:
                continue
            hits.append((rank, len(name), name, lat, lng))
        hits.sort()
        return [{"name": n, "lat": la, "lng": ln} for _, _, n, la, ln in hits[:limit]]

    def nearest_way(self, pt: LatLng, within_m: float = 25.0) -> dict | None:
        ci, cj = _cell(pt.lat, pt.lng)
        reach = int(within_m / 100) + 1
        best, best_d = None, within_m
        for i in range(ci - reach, ci + reach + 1):
            for j in range(cj - reach, cj + reach + 1):
                for wi, si in self._seg_index.get((i, j), ()):
                    g = self.ways[wi]["geom"]
                    d = point_segment_distance_m(pt, LatLng(lat=g[si][0], lng=g[si][1]), LatLng(lat=g[si + 1][0], lng=g[si + 1][1]))
                    if d < best_d:
                        best, best_d = self.ways[wi], d
        return best

    def pois_near(self, pt: LatLng, within_m: float) -> list[dict]:
        ci, cj = _cell(pt.lat, pt.lng)
        reach = int(within_m / (111_000 * CELL_DEG * max(0.3, cos(radians(pt.lat))))) + 1
        out = []
        for i in range(ci - reach, ci + reach + 1):
            for j in range(cj - reach, cj + reach + 1):
                for pi in self._poi_index.get((i, j), ()):
                    p = self.pois[pi]
                    if haversine_m(pt, LatLng(lat=p["lat"], lng=p["lng"])) <= within_m:
                        out.append(p)
        return out


_cache: dict[str, OsmStore | None] = {}


def get_store(path: str) -> OsmStore | None:
    if path not in _cache:
        _cache[path] = OsmStore.load(path)
    return _cache[path]
