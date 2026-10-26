import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { LogoMark, Wordmark } from "./Logo";
import { useAuth } from "../hooks/useAuth";

const links = [
  { to: "/navigate", label: "Navigate" },
  { to: "/safety-map", label: "Safety map" },
  { to: "/report", label: "Report" },
  { to: "/journeys", label: "Journeys" },
];

export default function AppShell({ children, fill = false }: { children: ReactNode; fill?: boolean }) {
  const { user, signOut } = useAuth();
  const cls = ({ isActive }: { isActive: boolean }) =>
    `rounded-full px-3 py-1.5 text-sm font-medium ${isActive ? "bg-plum text-white" : "text-plum hover:bg-lavender-soft"}`;
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-plum/10 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link to="/" className="flex items-center gap-2" aria-label="NariWay home">
            <LogoMark size={28} /><Wordmark className="text-xl" />
          </Link>
          <nav aria-label="Main" className="flex flex-wrap items-center gap-1">
            {links.map((l) => <NavLink key={l.to} to={l.to} className={cls}>{l.label}</NavLink>)}
            {user?.is_admin && <NavLink to="/admin" className={cls}>Admin</NavLink>}
          </nav>
          <div className="flex items-center gap-2 text-sm">
            {user ? (
              <>
                <NavLink to="/settings" className={cls}>{user.display_name.split(" ")[0]}</NavLink>
                <button onClick={signOut} className="text-plum/70 underline-offset-2 hover:underline">Sign out</button>
              </>
            ) : (
              <Link to="/account" className="btn-primary !px-4 !py-1.5">Sign in</Link>
            )}
          </div>
        </div>
      </header>
      <main className={fill ? "flex flex-1 flex-col" : "mx-auto w-full max-w-6xl flex-1 px-4 py-8"}>{children}</main>
      {!fill && (
        <footer className="border-t border-plum/10 bg-white py-4 text-center text-xs text-plum-ink/70">
          In an emergency, call <b>112</b>. NariWay is an early pilot: it informs your decisions and cannot guarantee safety.
        </footer>
      )}
    </div>
  );
}

export function NeedSignIn({ what }: { what: string }) {
  return (
    <div className="mx-auto max-w-md rounded-2xl bg-white p-8 text-center shadow-card">
      <h1 className="font-display text-2xl font-bold text-plum-deep">Sign in to continue</h1>
      <p className="mt-2 text-sm text-plum-ink/75">You need an account to {what}. Comparing routes works without one.</p>
      <Link to="/account" className="btn-primary mt-5">Sign in or create account</Link>
    </div>
  );
}
