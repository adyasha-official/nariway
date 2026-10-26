import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, setToken } from "../services/api";
import type { User } from "../types/api";

type Ctx = {
  user: User | null; loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signOut: () => void;
};
const AuthCtx = createContext<Ctx | null>(null);
const KEY = "nariway.token";

const store = {
  get: () => { try { return sessionStorage.getItem(KEY); } catch { return null; } },
  set: (v: string | null) => { try { v ? sessionStorage.setItem(KEY, v) : sessionStorage.removeItem(KEY); } catch { /* private mode */ } },
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = store.get();
    if (!t) { setLoading(false); return; }
    setToken(t);
    api.me().then(setUser).catch(() => { setToken(null); store.set(null); }).finally(() => setLoading(false));
  }, []);

  const accept = useCallback((r: { access_token: string; user: User }) => {
    setToken(r.access_token); store.set(r.access_token); setUser(r.user);
  }, []);

  const value = useMemo<Ctx>(() => ({
    user, loading,
    signIn: async (e, p) => accept(await api.login(e, p)),
    signUp: async (e, p, n) => accept(await api.register(e, p, n)),
    signOut: () => { setToken(null); store.set(null); setUser(null); },
  }), [user, loading, accept]);

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth(): Ctx {
  const c = useContext(AuthCtx);
  if (!c) throw new Error("useAuth outside AuthProvider");
  return c;
}
