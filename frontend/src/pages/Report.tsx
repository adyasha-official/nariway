import { useEffect, useState, type FormEvent } from "react";
import L from "leaflet";
import AppShell, { NeedSignIn } from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import { useMap } from "../hooks/useMap";
import { api } from "../services/api";
import { CATEGORY, ago } from "../lib/categories";
import type { Report as R } from "../types/api";

const WHEN = [
  { label: "Just now", mins: 0 }, { label: "Earlier today", mins: 240 },
  { label: "Yesterday", mins: 1440 }, { label: "In the last week", mins: 5760 },
];
const STATUS: Record<string, string> = {
  pending: "Awaiting review", approved: "Visible to others", rejected: "Not published", hidden: "Under review", expired: "Expired",
};

export default function Report() {
  const { user, loading } = useAuth();
  const { el, map } = useMap();
  const [pt, setPt] = useState<{ lat: number; lng: number } | null>(null);
  const [category, setCategory] = useState("poor_lighting");
  const [text, setText] = useState("");
  const [when, setWhen] = useState(0);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [mine, setMine] = useState<R[]>([]);

  const reload = () => api.myReports().then(setMine).catch(() => setMine([]));
  useEffect(() => { if (user) reload(); }, [user]);

  useEffect(() => {
    if (!map) return;
    let marker: L.CircleMarker | null = null;
    const h = (e: L.LeafletMouseEvent) => {
      marker?.remove();
      marker = L.circleMarker(e.latlng, { radius: 9, color: "#FF7F6E", fillColor: "#FF7F6E", fillOpacity: 0.9 }).addTo(map);
      setPt({ lat: e.latlng.lat, lng: e.latlng.lng });
    };
    map.on("click", h);
    return () => { map.off("click", h); marker?.remove(); };
  }, [map]);

  function locate() {
    if (!navigator.geolocation) { setMsg({ ok: false, text: "Your browser cannot share location. Click the map instead." }); return; }
    navigator.geolocation.getCurrentPosition(
      (p) => { map?.setView([p.coords.latitude, p.coords.longitude], 17); map?.fire("click", { latlng: L.latLng(p.coords.latitude, p.coords.longitude) }); },
      () => setMsg({ ok: false, text: "Location permission was denied. Click the map to place the report instead." }),
    );
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!pt) { setMsg({ ok: false, text: "Click the map to mark where this is." }); return; }
    setBusy(true); setMsg(null);
    try {
      await api.submitReport({ category, description: text, ...pt, occurred_at: new Date(Date.now() - WHEN[when].mins * 60000).toISOString() });
      setText(""); setMsg({ ok: true, text: "Thank you. Your report is awaiting review and will be shown to others once approved." });
      reload();
    } catch (x) { setMsg({ ok: false, text: (x as Error).message }); } finally { setBusy(false); }
  }

  if (loading) return <AppShell><p>Loading…</p></AppShell>;
  if (!user) return <AppShell><NeedSignIn what="report a concern" /></AppShell>;

  return (
    <AppShell>
      <h1 className="font-display text-3xl font-bold text-plum-deep">Report a concern</h1>
      <p className="mt-1 max-w-2xl text-sm text-plum-ink/75">
        Describe the <b>place</b>, not a person. Reports are reviewed before they are shown, expire after 90 days, and can be flagged by others.
      </p>
      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_420px]">
        <div ref={el} className="min-h-[360px] rounded-2xl shadow-card" aria-label="Map: click to mark the location" />
        <form onSubmit={submit} className="space-y-4 rounded-2xl bg-white p-5 shadow-card">
          <fieldset>
            <legend className="text-sm font-semibold">What did you notice?</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {Object.entries(CATEGORY).map(([k, v]) => (
                <button type="button" key={k} aria-pressed={category === k} onClick={() => setCategory(k)} title={v.hint}
                  className={`rounded-full px-3.5 py-1.5 text-sm ${category === k ? "bg-plum text-white" : "bg-lavender-soft text-plum"}`}>{v.label}</button>
              ))}
            </div>
          </fieldset>
          <label className="block text-sm font-semibold">Details (optional)
            <textarea value={text} onChange={(e) => setText(e.target.value)} maxLength={280} rows={3}
              placeholder="e.g. Street lamps not working between the market and the bus stop."
              className="mt-1 w-full rounded-xl border border-plum/20 p-3 text-sm font-normal outline-none focus:border-plum focus:ring-4 focus:ring-lavender" />
            <span className="text-xs font-normal text-plum-ink/60">{text.length}/280. No names, phone numbers, vehicle numbers or links.</span>
          </label>
          <label className="block text-sm font-semibold">When?
            <select value={when} onChange={(e) => setWhen(Number(e.target.value))} className="mt-1 w-full rounded-xl border border-plum/20 bg-white p-2.5 text-sm font-normal">
              {WHEN.map((w, i) => <option key={w.label} value={i}>{w.label}</option>)}
            </select>
          </label>
          <div className="flex items-center justify-between gap-2 rounded-xl bg-lavender-soft p-3 text-sm">
            <span>{pt ? `Location set (${pt.lat.toFixed(4)}, ${pt.lng.toFixed(4)})` : "Click the map to set the location"}</span>
            <button type="button" onClick={locate} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-plum">Use my location</button>
          </div>
          {msg && <p role={msg.ok ? "status" : "alert"} className={`rounded-xl p-3 text-sm ${msg.ok ? "bg-teal-soft text-teal-900" : "bg-coral-soft text-[#a63a2a]"}`}>{msg.text}</p>}
          <button className="btn-primary w-full" disabled={busy}>{busy ? "Sending…" : "Submit report"}</button>
          <p className="text-xs text-plum-ink/60">If someone is in danger now, call <b>112</b>. Reports are not monitored in real time.</p>
        </form>
      </div>

      {mine.length > 0 && (
        <section className="mt-10">
          <h2 className="font-display text-xl font-bold text-plum-deep">Your reports</h2>
          <ul className="mt-3 grid gap-3 md:grid-cols-2">
            {mine.map((r) => (
              <li key={r.id} className="rounded-2xl bg-white p-4 text-sm shadow-card">
                <div className="flex justify-between"><b>{CATEGORY[r.category]?.label ?? r.category}</b><span className="rounded-full bg-lavender px-2.5 py-0.5 text-xs font-semibold text-plum-deep">{STATUS[r.status] ?? r.status}</span></div>
                {r.description && <p className="mt-1 text-plum-ink/80">{r.description}</p>}
                <p className="mt-1 text-xs text-plum-ink/60">Observed {ago(r.occurred_at)}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </AppShell>
  );
}
