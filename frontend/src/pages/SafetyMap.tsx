import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import AppShell from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import { useMap } from "../hooks/useMap";
import { api } from "../services/api";
import { CATEGORY, ago } from "../lib/categories";
import type { Report } from "../types/api";

export default function SafetyMap() {
  const { user } = useAuth();
  const { el, map } = useMap();
  const layer = useRef<L.LayerGroup | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [note, setNote] = useState("");
  const [sel, setSel] = useState<Report | null>(null);
  const [flagMsg, setFlagMsg] = useState("");

  useEffect(() => {
    if (!map) return;
    layer.current = L.layerGroup().addTo(map);
    const load = () => {
      const b = map.getBounds();
      api.reportsIn({ min_lat: b.getSouth(), max_lat: b.getNorth(), min_lng: b.getWest(), max_lng: b.getEast() })
        .then((r) => { setReports(r); setNote(""); })
        .catch((e: Error) => { setReports([]); setNote(e.message); });
    };
    load();
    map.on("moveend", load);
    return () => { map.off("moveend", load); };
  }, [map]);

  useEffect(() => {
    const g = layer.current;
    if (!g) return;
    g.clearLayers();
    reports.forEach((r) =>
      L.circleMarker([r.lat, r.lng], { radius: 10, color: "#fff", weight: 2, fillColor: CATEGORY[r.category]?.color ?? "#999", fillOpacity: 0.95 })
        .on("click", () => { setSel(r); setFlagMsg(""); }).addTo(g));
  }, [reports]);

  async function flag(reason: string) {
    if (!sel) return;
    try { await api.flagReport(sel.id, reason); setFlagMsg("Thanks. A moderator will review this report."); }
    catch (e) { setFlagMsg((e as Error).message); }
  }

  return (
    <AppShell fill>
      <div className="grid flex-1 lg:grid-cols-[340px_1fr]">
        <aside className="space-y-4 overflow-auto bg-white/80 p-5">
          <h1 className="font-display text-2xl font-bold text-plum-deep">Safety map</h1>
          <p className="rounded-xl bg-lavender-soft p-3 text-sm text-plum-deep">
            <b>No markers does not mean an area is safe.</b> It only means nothing has been reported and approved here yet.
          </p>
          {note && <p role="status" className="text-sm text-[#a63a2a]">{note}</p>}
          <ul className="space-y-1.5 text-sm">
            {Object.entries(CATEGORY).map(([k, v]) => (
              <li key={k} className="flex items-center gap-2"><span className="h-3 w-3 rounded-full" style={{ background: v.color }} />{v.label}</li>
            ))}
          </ul>
          <p className="text-xs text-plum-ink/60">{reports.length} approved report{reports.length === 1 ? "" : "s"} in view. Reports expire after 90 days.</p>
          {sel && (
            <section className="rounded-2xl border border-plum/15 bg-white p-4 text-sm shadow-card" aria-live="polite">
              <div className="flex items-start justify-between gap-2">
                <b>{CATEGORY[sel.category]?.label ?? sel.category}</b>
                <button onClick={() => setSel(null)} aria-label="Close" className="text-plum/60">✕</button>
              </div>
              {sel.is_demo && <p className="mt-1 inline-block rounded-full bg-lavender px-2 py-0.5 text-xs font-semibold text-plum-deep">Sample data</p>}
              {sel.description && <p className="mt-2 text-plum-ink/85">{sel.description}</p>}
              <p className="mt-2 text-xs text-plum-ink/60">Observed {ago(sel.occurred_at)}</p>
              {!sel.is_demo && (user ? (
                <div className="mt-3">
                  <p className="text-xs font-semibold">Flag this report as:</p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {[["inaccurate", "Inaccurate"], ["identifies_person", "Identifies a person"], ["abusive", "Abusive"]].map(([k, l]) => (
                      <button key={k} onClick={() => flag(k)} className="rounded-full bg-coral-soft px-2.5 py-1 text-xs font-semibold text-[#a63a2a]">{l}</button>
                    ))}
                  </div>
                  {flagMsg && <p className="mt-2 text-xs">{flagMsg}</p>}
                </div>
              ) : <p className="mt-3 text-xs">Sign in to flag a report.</p>)}
            </section>
          )}
        </aside>
        <div ref={el} className="min-h-[480px]" aria-label="Safety map" />
      </div>
    </AppShell>
  );
}
