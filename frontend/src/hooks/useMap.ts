import { useEffect, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export const PILOT_CENTER: [number, number] = [22.2604, 84.8536];

/**
 * Creates one Leaflet map in the element given to `el` (use `ref={el}`).
 * A callback ref is used so the map is created whenever the element actually mounts,
 * including pages that render a loading state first.
 */
export function useMap(center: [number, number] = PILOT_CENTER, zoom = 13) {
  const [node, el] = useState<HTMLDivElement | null>(null);
  const [map, setMap] = useState<L.Map | null>(null);
  useEffect(() => {
    if (!node) return;
    const m = L.map(node).setView(center, zoom);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap contributors",
    }).addTo(m);
    setMap(m);
    return () => { m.remove(); setMap(null); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node]);
  return { el, map };
}
