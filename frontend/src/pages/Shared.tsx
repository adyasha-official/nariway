import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import L from "leaflet";
import { LogoMark, Wordmark } from "../components/Logo";
import { useMap } from "../hooks/useMap";
import { api } from "../services/api";
import { ago, clock } from "../lib/categories";
import type { SharedView } from "../types/api";

export default function Shared() {
  const { token = "" } = useParams();
  const [v, setV] = useState<SharedView | null>(null);
  const [gone, setGone] = useState(false);
  const { el, map } = useMap([22.2604, 84.8536], 14);

  useEffect(() => {
    const load = () => api.shared(token).then(setV).catch(() => { setV(null); setGone(true); });
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, [token]);

  useEffect(() => {
    if (!map || !v || v.last_lat == null || v.last_lng == null) return;
    const m = L.circleMarker([v.last_lat, v.last_lng], { radius: 10, color: "#fff", weight: 3, fillColor: "#6B21AB", fillOpacity: 1 }).addTo(map);
    map.setView([v.last_lat, v.last_lng], 15);
    return () => { m.remove(); };
  }, [map, v]);

  return (
    <div className="mx-auto min-h-screen max-w-xl px-4 py-6">
      <div className="mb-5 flex items-center gap-2"><LogoMark size={28} /><Wordmark className="text-xl" /></div>
      {gone && (
        <div className="rounded-2xl bg-white p-6 shadow-card" role="alert">
          <h1 className="font-display text-2xl font-bold text-plum-deep">This link is no longer active</h1>
          <p className="mt-2 text-sm">The journey may have ended, or the link was turned off or expired. If you are worried about someone, call them, or call <b>112</b> in an emergency.</p>
        </div>)}
      {v && (
        <div className="space-y-4">
          <div className="rounded-2xl bg-white p-6 shadow-card">
            <p className="text-sm text-plum-ink/70">{v.traveller} is travelling to</p>
            <h1 className="font-display text-3xl font-bold text-plum-deep">{v.destination}</h1>
            <p className={`mt-3 inline-block rounded-full px-3 py-1 text-sm font-semibold ${v.state === "overdue" ? "bg-coral-soft text-[#a63a2a]" : "bg-teal-soft text-teal-900"}`}>
              {v.state === "overdue" ? "Overdue" : "On the way"}
            </p>
            <p className="mt-3 text-sm">Expected by <b>{clock(v.expected_arrival)}</b></p>
            <p className="text-sm text-plum-ink/70">{v.last_checkin_at ? `Last check-in ${ago(v.last_checkin_at)}` : "No check-in yet"}</p>
          </div>
          {v.state === "overdue" && (
            <div className="rounded-2xl border border-coral bg-coral-soft p-4 text-sm text-[#7a2a1d]" role="alert">
              <b>{v.traveller} has not arrived yet.</b> Try calling {v.traveller} first. If you cannot reach {v.traveller} and are worried about safety, call <b>112</b>.
            </div>)}
          {v.last_lat != null && <div ref={el} className="h-64 overflow-hidden rounded-2xl shadow-card" aria-label="Last check-in location" />}
          <p className="text-xs text-plum-ink/60">{v.note} This page refreshes every 30 seconds.</p>
        </div>)}
    </div>
  );
}
