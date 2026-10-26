import { LogoMark } from "./Logo";

const palette = [
  { name: "Lavender", hex: "#E9D5FF", note: "Soft, modern, feminine" },
  { name: "Deep Plum", hex: "#6B21AB", note: "Trust, strength, confidence" },
  { name: "Coral", hex: "#FF7F6E", note: "Energy, warmth" },
  { name: "Teal", hex: "#14B8A6", note: "Safety, clarity, tech" },
];

export function Palette() {
  return (
    <section aria-labelledby="palette-h" className="rounded-3xl bg-white/80 p-6 shadow-card">
      <h2 id="palette-h" className="text-base font-semibold text-plum-ink">
        Our Color Palette
      </h2>
      <ul className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {palette.map((c) => (
          <li key={c.hex} className="flex flex-col items-center gap-1 text-center">
            <span className="h-16 w-16 rounded-full shadow-inner" style={{ background: c.hex }} />
            <span className="mt-1 text-xs font-semibold text-plum-ink">{c.name}</span>
            <span className="text-[10px] font-semibold text-plum-ink/80">{c.hex}</span>
            <span className="text-[10px] leading-tight text-plum-ink/60">{c.note}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function IconVariations() {
  return (
    <section aria-labelledby="icons-h" className="rounded-3xl bg-white/80 p-6 shadow-card">
      <h2 id="icons-h" className="text-base font-semibold text-plum-ink">
        App Icon Variations
      </h2>
      <div className="mt-4 flex gap-4">
        <span className="grid h-24 w-24 place-items-center rounded-3xl bg-white shadow-card">
          <LogoMark size={52} />
        </span>
        <span className="grid h-24 w-24 place-items-center rounded-3xl bg-plum shadow-card">
          <LogoMark size={52} variant="mono" paper="#FFFFFF" ink="#6B21AB" />
        </span>
        <span className="grid h-24 w-24 place-items-center rounded-3xl bg-gradient-to-br from-coral to-teal shadow-card">
          <LogoMark size={52} variant="mono" paper="#FFFFFF" ink="#14B8A6" />
        </span>
      </div>
    </section>
  );
}

export function TaglineCard() {
  return (
    <section
      className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#fbd9e6] via-[#f3d3f5] to-[#d9f0ec] p-8 shadow-card"
    >
      <svg viewBox="0 0 200 200" className="absolute -left-6 bottom-0 h-48 w-48 opacity-90" aria-hidden="true">
        <path d="M10 200C30 120 70 90 100 100c-20 20-10 60 20 100Z" fill="#14B8A6" />
        <path d="M40 200C50 140 90 120 130 140c-30 10-40 30-30 60Z" fill="#0f8f81" />
        <circle cx="130" cy="70" r="26" fill="#6B21AB" opacity=".75" />
        <path d="M110 60c10-18 40-14 48 6-12-6-22-4-32 8Z" fill="#4A1580" />
      </svg>
      <div className="relative ml-auto max-w-[14rem] font-display text-3xl font-semibold leading-snug">
        <p className="text-plum-ink">Safer</p>
        <p className="text-plum">Brighter</p>
        <p className="text-plum-deep">Stronger</p>
        <p className="text-coral">Together</p>
        <span className="mt-2 block h-0.5 w-8 bg-coral" />
      </div>
    </section>
  );
}
