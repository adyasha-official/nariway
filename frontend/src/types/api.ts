export type LatLng = { lat: number; lng: number };
export type Preference = "safety_first" | "balanced" | "fastest";
export type TravelMode = "walk" | "bike" | "cab";

export type Indicator = {
  key: string; label: string; value: number | null; coverage: number; source: string; note: string;
};
export type Candidate = { id: string; geometry: LatLng[]; duration_s: number; distance_m: number };
export type Assessment = {
  route_id: string; rank: number; cost: number; risk: number | null; uncertainty: number;
  evidence_coverage: number; confidence_label: "low" | "medium" | "higher"; labels: Preference[];
  excluded_for_detour: boolean; reasons: string[]; hazards: string[]; indicators: Indicator[];
};
export type AlternativesResponse = {
  is_demo: boolean; routing_source: string; pilot_city: string; routes: Candidate[];
  result: { model_version: string; disclaimer: string; is_demo: boolean;
            recommended: Record<Preference, string>; assessments: Assessment[] };
};
export type Place = { name: string; lat: number; lng: number };

export type User = { id: number; email: string; display_name: string; is_admin: boolean };
export type Report = {
  id: number; category: string; description: string; lat: number; lng: number;
  occurred_at: string; expires_at: string; status: string; is_demo: boolean;
};
export type AdminReport = Report & { flag_count: number; flag_reasons: string[] };
export type Contact = { id: number; name: string; contact_reference: string; consent_confirmed: boolean };
export type Trip = {
  id: number; origin_name: string; dest_name: string; preference: Preference; started_at: string;
  expected_arrival: string; state: "on_the_way" | "overdue" | "ended"; last_checkin_at: string | null;
};
export type Share = { id: number; contact_name: string | null; expires_at: string; revoked: boolean };
export type ShareCreated = { share_id: number; url: string; expires_at: string; contact_name: string | null };
export type SharedView = {
  traveller: string; destination: string; state: Trip["state"]; started_at: string; expected_arrival: string;
  last_checkin_at: string | null; last_lat: number | null; last_lng: number | null; note: string;
};
