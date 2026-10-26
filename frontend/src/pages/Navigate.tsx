import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import AppShell from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { getAlternatives, searchPlaces } from "../services/api";
import type { AlternativesResponse, Place, Preference, TravelMode } from "../types/api";

const MODES: { key: Preference; title: string; color: string; chip: string }[] = [
  { key: "safety_first", title: "Safest", color: "#14B8A6", chip: "bg-teal-soft text-teal-900" },
  { key: "balanced", title: "Balanced", color: "#6B21AB", chip: "bg-lavender text-plum-deep" },
  { key: "fastest", title: "Fastest", color: "#FF7F6E", chip: "bg-coral-soft text-[#a63a2a]" },
];
const TRAVEL: { key: TravelMode; label: string }[] = [
  { key: "walk", label: "Walk" }, { key: "bike", label: "Bike" }, { key: "cab", label: "Cab" },
];
const CENTER: [number, number] = [22.2604, 84.8536];

function PlaceInput({ label, value, onPick }: { label: string; value: Place | null; onPick: (p: Place) => void }) {
  const [text, setText] = useState(value?.name ?? "");
  const [opts, setOpts] = useState<Place[]>([]);
  useEffect(() => { setText(value?.name ?? ""); }, [value]);
  useEffect(() => {
    if (text.length < 2 || text === value?.name) { setOpts([]); return; }
    const t = setTimeout(() => searchPlaces(text).then(setOpts).catch(() => setOpts([])), 300);
    return () => clearTimeout(t);
  }, [text, value]);
  return (
    <div className="relative">
      <label className="mb-1 block text-xs font-semibold text-plum-ink/70">{label}</label>
      <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Search a place, or click the map"
        className="w-full rounded-xl border border-plum/20 bg-white px-3.5 py-2.5 text-sm outline-none focus:border-plum focus:ring-4 focus:ring-lavender" />
      {opts.length > 0 && (
        <ul className="absolute z-[1000] mt-1 max-h-56 w-full overflow-auto rounded-xl border border-plum/15 bg-white shadow-card">
          {opts.map((o) => (
            <li key={o.name + o.lat}>
              <button type="button" className="w-full px-3.5 py-2 text-left text-sm hover:bg-lavender-soft"
                onClick={() => { onPick(o); setOpts([]); }}>{o.name}</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Navigate() {
  const mapEl = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);
  const [origin, setOrigin] = useState<Place | null>(null);
  const [dest, setDest] = useState<Place | null>(null);
  const [mode, setMode] = useState<TravelMode>("walk");
  const [data, setData] = useState<AlternativesResponse | null>(null);
  const [pref, setPref] = useState<Preference>("balanced");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!mapEl.current || map.current) return;
    const m = L.map(mapEl.current).setView(CENTER, 13);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap contributors",
    }).addTo(m);
    layer.current = L.layerGroup().addTo(m);
    m.on("click", (e: L.LeafletMouseEvent) => {
      const p = { name: `${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)}`, lat: e.latlng.lat, lng: e.latlng.lng };
      setOrigin((o) => (o ? (setDest(p), o) : p));
    });
    map.current = m;
    return () => { m.remove(); map.current = null; };
  }, []);

  const byId = (id: string) => data?.result.assessments.find((a) => a.route_id === id);
  const selectedId = data?.result.recommended[pref];
  const selected = selectedId ? byId(selectedId) : undefined;

  useEffect(() => {
    const g = layer.current, m = map.current;
    if (!g || !m) return;
    g.clearLayers();
    if (origin) L.circleMarker([origin.lat, origin.lng], { radius: 8, color: "#6B21AB", fillColor: "#fff", fillOpacity: 1, weight: 3 }).addTo(g);
    if (dest) L.circleMarker([dest.lat, dest.lng], { radius: 8, color: "#FF7F6E", fillColor: "#FF7F6E", fillOpacity: 1, weight: 3 }).addTo(g);
    if (data) {
      const pts: L.LatLngExpression[] = [];
      [...data.routes].sort((a) => (a.id === selectedId ? 1 : -1)).forEach((r) => {
        const label = byId(r.id)?.labels[0];
        const color = MODES.find((x) => x.key === label)?.color ?? "#9a8aa8";
        const line = r.id === selectedId;
        const ll = r.geometry.map((p) => [p.lat, p.lng] as [number, number]);
        L.polyline(ll, { color, weight: line ? 7 : 4, opacity: line ? 0.95 : 0.45 }).addTo(g);
        pts.push(...ll);
      });
      m.fitBounds(L.latLngBounds(pts), { padding: [40, 40] });
    } else if (origin && dest) {
      m.fitBounds(L.latLngBounds([[origin.lat, origin.lng], [dest.lat, dest.lng]]), { padding: [60, 60] });
    }
  }); // eslint-disable-line react-hooks/exhaustive-deps

  const { user } = useAuth();
  const nav = useNavigate();
  const [startErr, setStartErr] = useState("");
  async function startJourney() {
    if (!dest || !origin || !data || !selectedId) return;
    const r = data.routes.find((x) => x.id === selectedId)!;
    const mins = Math.min(23 * 60, Math.ceil((r.duration_s / 60) * 1.25) + 5);
    try {
      await api.startTrip({ origin_name: origin.name, dest_name: dest.name, dest_lat: dest.lat, dest_lng: dest.lng,
        preference: pref, expected_arrival: new Date(Date.now() + mins * 60000).toISOString() });
      nav("/journeys");
    } catch (e) { setStartErr((e as Error).message); }
  }

  async function find() {
    if (!origin || !dest) return;
    setBusy(true); setError(""); setData(null);
    try { setData(await getAlternatives(origin, dest, mode)); }
    catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  return (
    <AppShell fill>
      <div className="grid flex-1 lg:grid-cols-[400px_1fr]">
        <aside className="flex flex-col gap-4 overflow-auto bg-white/80 p-5">
          <PlaceInput label="From" value={origin} onPick={setOrigin} />
          <PlaceInput label="To" value={dest} onPick={setDest} />
          <div className="flex gap-2" role="radiogroup" aria-label="Travel mode">
            {TRAVEL.map((t) => (
              <button key={t.key} role="radio" aria-checked={mode === t.key} onClick={() => setMode(t.key)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium ${mode === t.key ? "bg-plum text-white" : "bg-lavender-soft text-plum"}`}>{t.label}</button>
            ))}
          </div>
          <button className="btn-primary" disabled={!origin || !dest || busy} onClick={find}>
            {busy ? "Finding routes…" : "Compare routes"}
          </button>
          {error && <p role="alert" className="rounded-xl bg-coral-soft p-3 text-sm text-[#a63a2a]">{error}</p>}

          {data && selected && (
            <>
              {data.is_demo && (
                <p className="rounded-xl border border-dashed border-plum/40 bg-lavender-soft p-3 text-xs text-plum-deep">
                  <b>Sample data.</b> These routes and safety indicators are demonstration data, not real conditions.
                </p>
              )}
              <div className="grid gap-2">
                {MODES.map((m) => {
                  const a = byId(data.result.recommended[m.key])!;
                  const r = data.routes.find((x) => x.id === a.route_id)!;
                  return (
                    <button key={m.key} onClick={() => setPref(m.key)} aria-pressed={pref === m.key}
                      className={`flex items-center justify-between rounded-2xl border p-3 text-left ${pref === m.key ? "border-plum shadow-card" : "border-plum/10"} bg-white`}>
                      <span><span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${m.chip}`}>{m.title}</span>
                        <span className="mt-1 block text-xs text-plum-ink/70">{(r.distance_m / 1000).toFixed(1)} km · {a.confidence_label} confidence</span></span>
                      <span className="text-lg font-semibold">{Math.round(r.duration_s / 60)} min</span>
                    </button>
                  );
                })}
              </div>
              <section className="rounded-2xl bg-lavender-soft p-4 text-sm">
                <h2 className="font-semibold text-plum-deep">Why this route</h2>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-plum-ink/85">{selected.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
                <h3 className="mt-3 font-semibold text-plum-deep">Evidence</h3>
                <ul className="mt-1 space-y-1">
                  {selected.indicators.map((i) => (
                    <li key={i.key} className="flex justify-between gap-3">
                      <span>{i.label}</span>
                      <span className="text-plum-ink/70">{i.value === null ? "Unknown" : i.value < 0.34 ? "Fewer concerns" : i.value < 0.67 ? "Mixed" : "Concerns"} · {Math.round(i.coverage * 100)}% covered</span>
                    </li>
                  ))}
                </ul>
                {selected.hazards.length > 0 && (
                  <><h3 className="mt-3 font-semibold text-[#a63a2a]">Known concerns</h3>
                  <ul className="list-disc pl-5">{selected.hazards.map((h) => <li key={h}>{h}</li>)}</ul></>
                )}
              </section>
              {user ? (
                <button className="btn-primary" onClick={startJourney}>Start this journey</button>
              ) : (
                <Link className="btn-outline" to="/account?next=/navigate">Sign in to start and share this journey</Link>
              )}
              {startErr && <p role="alert" className="text-sm text-[#a63a2a]">{startErr}</p>}
              <p className="text-xs text-plum-ink/60">{data.result.disclaimer}</p>
            </>
          )}
        </aside>
        <div ref={mapEl} className="min-h-[420px]" aria-label="Map" />
      </div>
    </AppShell>
  );
}
