import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell, { NeedSignIn } from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";

export default function Settings() {
  const { user, loading, signOut } = useAuth();
  const nav = useNavigate();
  const [confirm, setConfirm] = useState("");
  const [err, setErr] = useState("");
  if (loading) return <AppShell><p>Loading…</p></AppShell>;
  if (!user) return <AppShell><NeedSignIn what="manage your settings" /></AppShell>;

  async function erase() {
    try { await api.deleteAccount(); signOut(); nav("/", { replace: true }); } catch (e) { setErr((e as Error).message); }
  }
  return (
    <AppShell>
      <h1 className="font-display text-3xl font-bold text-plum-deep">Settings & privacy</h1>
      <div className="mt-6 grid gap-6 md:grid-cols-2">
        <section className="rounded-2xl bg-white p-6 shadow-card">
          <h2 className="font-semibold">Your account</h2>
          <p className="mt-2 text-sm">{user.display_name}<br /><span className="text-plum-ink/70">{user.email}</span></p>
          <button onClick={signOut} className="btn-outline mt-4 !py-2">Sign out</button>
        </section>
        <section className="rounded-2xl bg-white p-6 shadow-card">
          <h2 className="font-semibold">What NariWay keeps</h2>
          <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm text-plum-ink/85">
            <li>Route searches are <b>not stored</b>. Comparing routes works without an account.</li>
            <li>A journey stores only its destination and times. The last check-in location is erased when you end it.</li>
            <li>Share links are random, stored only as a hash, expire, and stop working when you end the journey.</li>
            <li>Reports you submit stay available to others after approval, <b>without your name</b>.</li>
          </ul>
        </section>
        <section className="rounded-2xl border border-coral/40 bg-white p-6 shadow-card md:col-span-2">
          <h2 className="font-semibold text-[#a63a2a]">Delete my account</h2>
          <p className="mt-2 text-sm">This permanently erases your account, trusted contacts, journeys and share links. Your approved reports stay on the map but are no longer linked to you.</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <input value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder='Type "delete" to confirm' className="rounded-lg border border-plum/20 p-2 text-sm" aria-label="Type delete to confirm" />
            <button disabled={confirm !== "delete"} onClick={erase} className="rounded-full bg-[#c2412f] px-5 py-2 text-sm font-semibold text-white disabled:opacity-40">Delete everything</button>
          </div>
          {err && <p role="alert" className="mt-2 text-sm text-[#a63a2a]">{err}</p>}
        </section>
      </div>
    </AppShell>
  );
}
