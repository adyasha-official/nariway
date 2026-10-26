import { useCallback, useEffect, useState, type FormEvent } from "react";
import AppShell, { NeedSignIn } from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import { clock } from "../lib/categories";
import type { Contact, Share, ShareCreated, Trip } from "../types/api";

const STATE: Record<Trip["state"], { label: string; cls: string }> = {
  on_the_way: { label: "On the way", cls: "bg-teal-soft text-teal-900" },
  overdue: { label: "Overdue", cls: "bg-coral-soft text-[#a63a2a]" },
  ended: { label: "Ended", cls: "bg-lavender text-plum-deep" },
};

function TripCard({ trip, contacts, onChange }: { trip: Trip; contacts: Contact[]; onChange: () => void }) {
  const [shares, setShares] = useState<Share[]>([]);
  const [created, setCreated] = useState<ShareCreated | null>(null);
  const [contactId, setContactId] = useState("");
  const [hours, setHours] = useState(6);
  const [msg, setMsg] = useState("");
  const active = trip.state !== "ended";

  const loadShares = useCallback(() => { if (active) api.shares(trip.id).then(setShares).catch(() => setShares([])); }, [trip.id, active]);
  useEffect(loadShares, [loadShares]);

  const run = async (fn: () => Promise<unknown>, ok = "") => {
    setMsg("");
    try { await fn(); if (ok) setMsg(ok); onChange(); loadShares(); } catch (e) { setMsg((e as Error).message); }
  };

  function checkIn(withLocation: boolean) {
    if (!withLocation) return run(() => api.checkIn(trip.id, {}), "Checked in.");
    if (!navigator.geolocation) return setMsg("Your browser cannot share location.");
    navigator.geolocation.getCurrentPosition(
      (p) => run(() => api.checkIn(trip.id, { lat: p.coords.latitude, lng: p.coords.longitude }), "Checked in with your location."),
      () => setMsg("Location permission denied. You can still check in without it."),
    );
  }
  const extend = () => run(() => api.checkIn(trip.id, { expected_arrival: new Date(new Date(trip.expected_arrival).getTime() + 15 * 60000).toISOString() }), "Added 15 minutes.");

  async function share() {
    setMsg("");
    try { setCreated(await api.share(trip.id, { contact_id: contactId ? Number(contactId) : undefined, hours })); loadShares(); }
    catch (e) { setMsg((e as Error).message); }
  }
  const contact = contacts.find((c) => c.name === created?.contact_name);
  const text = created ? `Follow my journey to ${trip.dest_name} on NariWay: ${created.url}` : "";
  const digits = contact?.contact_reference.replace(/\D/g, "") ?? "";

  return (
    <li className="rounded-2xl bg-white p-5 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-lg font-semibold text-plum-ink">To {trip.dest_name}</h3>
          <p className="text-sm text-plum-ink/70">From {trip.origin_name} · expected by {clock(trip.expected_arrival)}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATE[trip.state].cls}`}>{STATE[trip.state].label}</span>
      </div>
      {trip.last_checkin_at && <p className="mt-1 text-xs text-plum-ink/60">Last check-in {clock(trip.last_checkin_at)}</p>}
      {active && (
        <>
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn-primary !py-2" onClick={() => checkIn(false)}>I'm OK</button>
            <button className="btn-outline !py-2" onClick={() => checkIn(true)}>Check in with location</button>
            <button className="btn-outline !py-2" onClick={extend}>+15 min</button>
            <button className="btn-outline !border-coral !py-2 !text-[#a63a2a]" onClick={() => run(() => api.endTrip(trip.id))}>I've arrived · end journey</button>
          </div>

          <div className="mt-5 rounded-xl bg-lavender-soft p-4">
            <h4 className="text-sm font-semibold text-plum-deep">Share this journey</h4>
            <div className="mt-2 flex flex-wrap items-end gap-2 text-sm">
              <label>With
                <select value={contactId} onChange={(e) => setContactId(e.target.value)} className="ml-2 rounded-lg border border-plum/20 bg-white p-1.5">
                  <option value="">Anyone with the link</option>
                  {contacts.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select></label>
              <label>For
                <select value={hours} onChange={(e) => setHours(Number(e.target.value))} className="ml-2 rounded-lg border border-plum/20 bg-white p-1.5">
                  {[1, 3, 6, 12, 24].map((h) => <option key={h} value={h}>{h} h</option>)}</select></label>
              <button className="btn-primary !py-1.5" onClick={share}>Create link</button>
            </div>
            {created && (
              <div className="mt-3 rounded-xl border border-plum/20 bg-white p-3 text-sm" role="status">
                <p className="font-semibold">Link created. It is shown only once, so send it now.</p>
                <input readOnly value={created.url} onFocus={(e) => e.target.select()} className="mt-2 w-full rounded-lg border border-plum/20 p-2 text-xs" aria-label="Share link" />
                <div className="mt-2 flex flex-wrap gap-2">
                  <button className="btn-outline !py-1.5 !text-xs" onClick={() => navigator.clipboard?.writeText(created.url).then(() => setMsg("Link copied."))}>Copy</button>
                  <a className="btn-outline !py-1.5 !text-xs" target="_blank" rel="noreferrer" href={`https://wa.me/${digits}?text=${encodeURIComponent(text)}`}>WhatsApp</a>
                  <a className="btn-outline !py-1.5 !text-xs" href={`sms:${contact?.contact_reference ?? ""}?body=${encodeURIComponent(text)}`}>SMS</a>
                </div>
              </div>
            )}
            {shares.filter((s) => !s.revoked && new Date(s.expires_at) > new Date()).map((s) => (
              <p key={s.id} className="mt-2 flex items-center justify-between text-sm">
                <span>{s.contact_name ?? "Link"} · until {clock(s.expires_at)}</span>
                <button className="text-xs font-semibold text-[#a63a2a] underline" onClick={() => run(() => api.revokeShare(trip.id, s.id), "Link turned off.")}>Turn off</button>
              </p>))}
          </div>
        </>
      )}
      {msg && <p role="status" className="mt-3 text-sm text-plum-ink/80">{msg}</p>}
    </li>
  );
}

export default function Journeys() {
  const { user, loading } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [f, setF] = useState({ name: "", ref: "", consent: false });
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    api.trips().then(setTrips).catch(() => setTrips([]));
    api.contacts().then(setContacts).catch(() => setContacts([]));
  }, []);
  useEffect(() => { if (user) load(); }, [user, load]);
  useEffect(() => { if (!user) return; const t = setInterval(() => api.trips().then(setTrips).catch(() => {}), 30000); return () => clearInterval(t); }, [user]);

  async function addContact(e: FormEvent) {
    e.preventDefault(); setErr("");
    try { await api.addContact({ name: f.name, contact_reference: f.ref, consent_confirmed: f.consent }); setF({ name: "", ref: "", consent: false }); load(); }
    catch (x) { setErr((x as Error).message); }
  }

  if (loading) return <AppShell><p>Loading…</p></AppShell>;
  if (!user) return <AppShell><NeedSignIn what="use Journey Guardian" /></AppShell>;
  const active = trips.filter((t) => t.state !== "ended");

  return (
    <AppShell>
      <h1 className="font-display text-3xl font-bold text-plum-deep">Journey Guardian</h1>
      <p className="mt-1 max-w-2xl rounded-xl bg-lavender-soft p-3 text-sm text-plum-deep">
        <b>How this works:</b> you send a private link to someone you trust. They see your destination, expected arrival and your last check-in. It is <b>not live tracking</b>, and NariWay does <b>not</b> send alerts automatically yet. If you go overdue, the link shows it. In an emergency, call <b>112</b>.
      </p>
      <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_340px]">
        <section>
          <h2 className="font-display text-xl font-bold text-plum-deep">Active journeys</h2>
          {active.length === 0 ? (
            <p className="mt-3 rounded-2xl bg-white p-6 text-sm shadow-card">No active journey. Pick a route on the Navigate page and choose “Start this journey”.</p>
          ) : <ul className="mt-3 space-y-4">{active.map((t) => <TripCard key={t.id} trip={t} contacts={contacts} onChange={load} />)}</ul>}
          {trips.some((t) => t.state === "ended") && (
            <p className="mt-6 text-xs text-plum-ink/60">{trips.filter((t) => t.state === "ended").length} past journey(ies) kept without location. Delete your account in Settings to erase them.</p>)}
        </section>
        <aside>
          <h2 className="font-display text-xl font-bold text-plum-deep">Trusted contacts</h2>
          <ul className="mt-3 space-y-2">
            {contacts.map((c) => (
              <li key={c.id} className="flex items-center justify-between rounded-xl bg-white p-3 text-sm shadow-card">
                <span><b>{c.name}</b><br /><span className="text-plum-ink/60">{c.contact_reference}</span></span>
                <button className="text-xs text-[#a63a2a] underline" onClick={() => api.removeContact(c.id).then(load)}>Remove</button>
              </li>))}
          </ul>
          <form onSubmit={addContact} className="mt-3 space-y-2 rounded-2xl bg-white p-4 text-sm shadow-card">
            <input required placeholder="Name" maxLength={60} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} className="w-full rounded-lg border border-plum/20 p-2" />
            <input required placeholder="Phone or email" maxLength={80} value={f.ref} onChange={(e) => setF({ ...f, ref: e.target.value })} className="w-full rounded-lg border border-plum/20 p-2" />
            <label className="flex gap-2 text-xs"><input type="checkbox" checked={f.consent} onChange={(e) => setF({ ...f, consent: e.target.checked })} />
              This person has agreed to be my trusted contact.</label>
            {err && <p role="alert" className="text-xs text-[#a63a2a]">{err}</p>}
            <button className="btn-outline w-full !py-2">Add contact</button>
          </form>
        </aside>
      </div>
    </AppShell>
  );
}
