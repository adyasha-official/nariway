export const CATEGORY: Record<string, { label: string; color: string; hint: string }> = {
  poor_lighting: { label: "Poor lighting", color: "#6B21AB", hint: "Lamps out or very dark" },
  isolated: { label: "Isolated stretch", color: "#14B8A6", hint: "Few people around" },
  harassment: { label: "Harassment reported", color: "#FF7F6E", hint: "Describe the place, not the person" },
  unsafe_crossing: { label: "Unsafe crossing", color: "#D97706", hint: "Hard to cross safely" },
  obstruction: { label: "Blocked footpath", color: "#64748B", hint: "Path blocked or broken" },
  other: { label: "Other concern", color: "#9CA3AF", hint: "Something else about this place" },
};

export function ago(iso: string): string {
  const mins = Math.max(0, (Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 60) return `${Math.round(mins)} min ago`;
  if (mins < 60 * 48) return `${Math.round(mins / 60)} h ago`;
  return `${Math.round(mins / 1440)} days ago`;
}

export const clock = (iso: string) =>
  new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
