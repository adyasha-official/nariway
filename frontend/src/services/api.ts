import type {
  AdminReport, AlternativesResponse, Contact, LatLng, Place, Report, Share, ShareCreated, SharedView,
  Trip, TravelMode, User, Preference,
} from "../types/api";

let token: string | null = null;
export const setToken = (t: string | null) => { token = t; };

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

async function req<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const res = await fetch(`/api/v1${path}`, {
    method,
    headers: { ...(body ? { "Content-Type": "application/json" } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let msg = "Something went wrong. Please try again.";
    try {
      const b = await res.json();
      if (typeof b.detail === "string") msg = b.detail;
      else if (Array.isArray(b.detail) && b.detail[0]?.msg) msg = String(b.detail[0].msg).replace(/^Value error, /, "");
    } catch { /* keep default */ }
    throw new ApiError(msg, res.status);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

type Bounds = { min_lat: number; max_lat: number; min_lng: number; max_lng: number };
const qs = (o: Record<string, string | number>) => new URLSearchParams(Object.entries(o).map(([k, v]) => [k, String(v)])).toString();

export const api = {
  searchPlaces: (q: string) => req<Place[]>(`/places/search?${qs({ q })}`),
  alternatives: (origin: LatLng, destination: LatLng, mode: TravelMode) =>
    req<AlternativesResponse>("/routes/alternatives", "POST", { origin, destination, mode }),
  register: (email: string, password: string, display_name: string) =>
    req<{ access_token: string; user: User }>("/auth/register", "POST", { email, password, display_name }),
  login: (email: string, password: string) => req<{ access_token: string; user: User }>("/auth/login", "POST", { email, password }),
  me: () => req<User>("/auth/me"),
  deleteAccount: () => req<void>("/auth/me", "DELETE"),
  categories: () => req<string[]>("/safety/categories"),
  submitReport: (b: { category: string; description: string; lat: number; lng: number; occurred_at: string }) =>
    req<Report>("/safety/reports", "POST", b),
  reportsIn: (b: Bounds) => req<Report[]>(`/safety/reports?${qs(b)}`),
  myReports: () => req<Report[]>("/safety/reports/mine"),
  flagReport: (id: number, reason: string) => req<void>(`/safety/reports/${id}/flag`, "POST", { reason }),
  contacts: () => req<Contact[]>("/contacts"),
  addContact: (b: Omit<Contact, "id">) => req<Contact>("/contacts", "POST", b),
  removeContact: (id: number) => req<void>(`/contacts/${id}`, "DELETE"),
  trips: () => req<Trip[]>("/trips"),
  startTrip: (b: { origin_name: string; dest_name: string; dest_lat: number; dest_lng: number; preference: Preference; expected_arrival: string }) =>
    req<Trip>("/trips", "POST", b),
  checkIn: (id: number, b: { lat?: number; lng?: number; expected_arrival?: string }) => req<Trip>(`/trips/${id}/check-in`, "POST", b),
  endTrip: (id: number) => req<Trip>(`/trips/${id}/end`, "POST"),
  share: (id: number, b: { contact_id?: number; hours?: number }) => req<ShareCreated>(`/trips/${id}/share`, "POST", b),
  shares: (id: number) => req<Share[]>(`/trips/${id}/shares`),
  revokeShare: (id: number, shareId: number) => req<void>(`/trips/${id}/shares/${shareId}`, "DELETE"),
  shared: (tok: string) => req<SharedView>(`/shared/${encodeURIComponent(tok)}`),
  adminReports: (status: string) => req<AdminReport[]>(`/admin/reports?status=${status}`),
  moderate: (id: number, action: "approve" | "reject", note: string) =>
    req<AdminReport>(`/admin/reports/${id}/moderate`, "POST", { action, note }),
  adminStats: () => req<Record<string, unknown>>("/admin/stats"),
  adminAudit: () => req<{ at: string; action: string; target: string; note: string }[]>("/admin/audit"),
};

// Back-compat for the Navigate page written earlier.
export const searchPlaces = api.searchPlaces;
export const getAlternatives = api.alternatives;
