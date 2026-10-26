import { useState, type FormEvent } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import AppShell from "../components/AppShell";
import { useAuth } from "../hooks/useAuth";

export default function Account() {
  const { user, signIn, signUp } = useAuth();
  const nav = useNavigate();
  const next = useSearchParams()[0].get("next") || "/navigate";
  const [mode, setMode] = useState<"in" | "up">("in");
  const [f, setF] = useState({ email: "", password: "", name: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to={next} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      if (mode === "in") await signIn(f.email, f.password); else await signUp(f.email, f.password, f.name);
      nav(next, { replace: true });
    } catch (x) { setErr((x as Error).message); } finally { setBusy(false); }
  }
  const field = "w-full rounded-xl border border-plum/20 bg-white px-3.5 py-2.5 text-sm outline-none focus:border-plum focus:ring-4 focus:ring-lavender";

  return (
    <AppShell>
      <form onSubmit={submit} className="mx-auto max-w-sm rounded-2xl bg-white p-7 shadow-card">
        <h1 className="font-display text-2xl font-bold text-plum-deep">{mode === "in" ? "Welcome back" : "Create your account"}</h1>
        <p className="mt-1 text-sm text-plum-ink/70">An account is only needed for reports and Journey Guardian.</p>
        <div className="mt-5 space-y-3">
          {mode === "up" && (
            <label className="block text-sm font-medium">Name
              <input className={field} required maxLength={60} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} autoComplete="given-name" />
            </label>)}
          <label className="block text-sm font-medium">Email
            <input className={field} type="email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} autoComplete="email" />
          </label>
          <label className="block text-sm font-medium">Password
            <input className={field} type="password" required minLength={8} maxLength={72} value={f.password}
              onChange={(e) => setF({ ...f, password: e.target.value })} autoComplete={mode === "in" ? "current-password" : "new-password"} />
            {mode === "up" && <span className="text-xs text-plum-ink/60">At least 8 characters.</span>}
          </label>
        </div>
        {err && <p role="alert" className="mt-3 rounded-xl bg-coral-soft p-3 text-sm text-[#a63a2a]">{err}</p>}
        <button className="btn-primary mt-5 w-full" disabled={busy}>{busy ? "Please wait…" : mode === "in" ? "Sign in" : "Create account"}</button>
        <button type="button" className="mt-3 w-full text-sm text-plum underline-offset-2 hover:underline"
          onClick={() => { setMode(mode === "in" ? "up" : "in"); setErr(""); }}>
          {mode === "in" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
      </form>
    </AppShell>
  );
}
