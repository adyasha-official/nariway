import { useCallback, useEffect, useState } from "react";
import AppShell, { NeedSignIn } from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { CATEGORY, ago } from "../lib/categories";
import type { AdminReport } from "../types/api";

const TABS = ["pending", "hidden", "approved", "rejected"] as const;

export default function Admin() {
  const { user, loading } = useAuth();
  const [tab, setTab] = useState<(typeof TABS)[number]>("pending");
  const [rows, setRows] = useState<AdminReport[]>([]);
  const [stats, setStats] = useState<Record<string, unknown>>({});
  const [audit, setAudit] = useState<{ at: string; action: string; target: string; note: string }[]>([]);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    api.adminReports(tab).then(setRows).catch((e: Error) => setErr(e.message));
    api.adminStats().then(setStats).catch(() => {});
    api.adminAudit().then(setAudit).catch(() => {});
  }, [tab]);
  useEffect(() => { if (user?.is_admin) load(); }, [user, load]);

  if (loading) return <AppShell><p>Loading…</p></AppShell>;
  if (!user) return <AppShell><NeedSignIn what="open the moderation area" /></AppShell>;
  if (!user.is_admin) return <AppShell><p role="alert" className="rounded-2xl bg-white p-6 shadow-card">You do not have access to this area.</p></AppShell>;

  const act = (id: number, action: "approve" | "reject") =>
    api.moderate(id, action, notes[id] ?? "").then(load).catch((e: Error) => setErr(e.message));

  return (
    <AppShell>
      <h1 className="font-display text-3xl font-bold text-plum-deep">Moderation</h1>
      <p className="mt-1 max-w-3xl text-sm text-plum-ink/75">
        Approve only observations about <b>places</b>. Reject reports that name or describe a person, target a community or neighbourhood, contain contact details, or look retaliatory.
      </p>
      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        {Object.entries((stats.reports_by_status as Record<string, number>) ?? {}).map(([k, n]) => (
          <span key={k} className="rounded-full bg-white px-3 py-1 shadow-card">{k}: <b>{n}</b></span>))}
        <span className="rounded-full bg-white px-3 py-1 shadow-card">users: <b>{String(stats.users ?? 0)}</b></span>
        <span className="rounded-full bg-white px-3 py-1 shadow-card">sample reports: <b>{String(stats.sample_reports ?? 0)}</b></span>
      </div>
      <div className="mt-5 flex gap-2" role="tablist">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
            className={`rounded-full px-4 py-1.5 text-sm capitalize ${tab === t ? "bg-plum text-white" : "bg-lavender-soft text-plum"}`}>{t}</button>))}
      </div>
      {err && <p role="alert" className="mt-3 text-sm text-[#a63a2a]">{err}</p>}
      <ul className="mt-4 grid gap-3 md:grid-cols-2">
        {rows.length === 0 && <li className="text-sm text-plum-ink/70">Nothing in this queue.</li>}
        {rows.map((r) => (
          <li key={r.id} className="rounded-2xl bg-white p-4 text-sm shadow-card">
            <div className="flex justify-between"><b>{CATEGORY[r.category]?.label ?? r.category}</b><span className="text-xs text-plum-ink/60">{ago(r.occurred_at)}</span></div>
            <p className="mt-1">{r.description || <i className="text-plum-ink/50">No description</i>}</p>
            <p className="mt-1 text-xs text-plum-ink/60">{r.lat.toFixed(4)}, {r.lng.toFixed(4)}{r.flag_count > 0 && ` · ${r.flag_count} flag(s): ${r.flag_reasons.join(", ")}`}</p>
            <input value={notes[r.id] ?? ""} onChange={(e) => setNotes({ ...notes, [r.id]: e.target.value })} maxLength={300} placeholder="Note (kept in audit log)" className="mt-2 w-full rounded-lg border border-plum/20 p-1.5 text-xs" />
            <div className="mt-2 flex gap-2">
              {tab !== "approved" && <button className="btn-primary !px-4 !py-1.5 !text-xs" onClick={() => act(r.id, "approve")}>Approve</button>}
              {tab !== "rejected" && <button className="btn-outline !px-4 !py-1.5 !text-xs" onClick={() => act(r.id, "reject")}>Reject</button>}
            </div>
          </li>))}
      </ul>
      <h2 className="mt-10 font-display text-xl font-bold text-plum-deep">Audit log</h2>
      <ul className="mt-2 space-y-1 text-xs text-plum-ink/80">
        {audit.map((a, i) => <li key={i}>{new Date(a.at).toLocaleString()} · {a.action} · {a.target}{a.note && ` · “${a.note}”`}</li>)}
      </ul>
    </AppShell>
  );
}
