import { Bell, Bike, Bus, Car, Menu, Person, Pin, Swap, Walk, ShieldTeal, Bolt, Scales } from "./Icons";
import { LogoMark, Wordmark } from "./Logo";

const modes = [
  { label: "NariWay", icon: <Person />, active: true },
  { label: "Walk", icon: <Walk /> },
  { label: "Public Transport", icon: <Bus /> },
  { label: "Bike", icon: <Bike /> },
  { label: "Cab", icon: <Car /> },
];

/** Static preview. Routes shown here are illustrative sample data, not real routing output. */
export default function PhoneMockup() {
  return (
    <div className="relative mx-auto w-[300px] rounded-[2.8rem] border-[7px] border-plum-ink bg-white shadow-phone">
      <div className="absolute left-1/2 top-2 z-20 h-6 w-24 -translate-x-1/2 rounded-full bg-plum-ink" />
      <div className="overflow-hidden rounded-[2.2rem] bg-white">
        <div className="flex items-center justify-between px-5 pb-1 pt-3 text-[10px] font-semibold text-plum-ink">
          <span>9:41</span>
          <span aria-hidden="true">●●● ▮</span>
        </div>

        <div className="flex items-center justify-between px-4 py-2">
          <Menu />
          <div className="flex items-center gap-1.5">
            <LogoMark size={20} />
            <Wordmark className="text-lg" />
          </div>
          <Bell />
        </div>

        <div className="mx-3 flex items-center gap-2">
          <div className="flex-1 space-y-1.5">
            <div className="flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-[11px] text-plum-ink shadow-card">
              <Pin /> Your location
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-white px-3 py-2 text-[11px] text-plum-ink/70 shadow-card">
              <Pin /> Destination
            </div>
          </div>
          <button type="button" aria-label="Swap origin and destination" className="rounded-xl bg-white p-2 shadow-card">
            <Swap />
          </button>
        </div>

        <div className="mt-3 flex justify-between px-3">
          {modes.map((m) => (
            <div key={m.label} className="flex w-[52px] flex-col items-center gap-1">
              <span
                className={`grid h-10 w-11 place-items-center rounded-xl ${
                  m.active ? "bg-plum text-white" : "bg-lavender-soft text-plum"
                }`}
              >
                {m.icon}
              </span>
              <span className="text-center text-[8px] leading-tight text-plum-ink/80">{m.label}</span>
            </div>
          ))}
        </div>

        {/* map */}
        <div className="relative mt-3 h-[210px] overflow-hidden bg-[#eef0ea]">
          <svg viewBox="0 0 300 210" className="absolute inset-0 h-full w-full" aria-hidden="true">
            <g stroke="#fff" strokeWidth="6" fill="none" opacity=".9">
              <path d="M0 60 300 40M0 140 300 120M60 0 90 210M170 0 190 210M250 0 240 210" />
            </g>
            <g stroke="#d9dccf" strokeWidth="1.5" fill="none">
              <path d="M0 100 300 90M0 180 300 170M120 0 130 210M30 0 40 210" />
            </g>
            <rect x="196" y="140" width="70" height="40" rx="8" fill="#cfe8d2" opacity=".8" />
            {/* fastest */}
            <path d="M52 178 100 112 140 118 168 82 212 70 232 40" stroke="#FF7F6E" strokeWidth="3.5" fill="none" strokeLinejoin="round" />
            {/* balanced */}
            <path d="M52 178 128 150 164 96 214 82 232 40" stroke="#6B21AB" strokeWidth="3.5" fill="none" strokeLinejoin="round" />
            {/* safest */}
            <path d="M52 178 84 190 150 168 200 146 238 110 232 40" stroke="#14B8A6" strokeWidth="3.5" fill="none" strokeLinejoin="round" />
            <circle cx="52" cy="178" r="7" fill="#4F46E5" stroke="#fff" strokeWidth="3" />
            <circle cx="232" cy="40" r="6" fill="#6B21AB" stroke="#fff" strokeWidth="3" />
          </svg>
          <span className="absolute right-3 top-2 flex items-center gap-1 text-[9px] font-semibold text-plum-ink">
            <Pin className="h-3 w-3" /> Destination
          </span>
          <span className="absolute left-2 top-5 rounded-lg bg-coral px-2 py-1 text-center text-[9px] font-bold leading-tight text-white shadow">
            Fastest<br />
            <span className="text-[11px]">18 min</span>
            <br />
            <span className="font-medium">Shows hazards</span>
          </span>
          <span className="absolute right-3 top-[88px] rounded-lg bg-plum px-2 py-1 text-center text-[9px] font-bold leading-tight text-white shadow">
            Balanced<br />
            <span className="text-[11px]">25 min</span>
            <br />
            <span className="font-medium">Mixed evidence</span>
          </span>
          <span className="absolute bottom-6 right-6 rounded-lg bg-teal px-2 py-1 text-center text-[9px] font-bold leading-tight text-white shadow">
            Safety First<br />
            <span className="text-[11px]">32 min</span>
            <br />
            <span className="font-medium">Most evidence</span>
          </span>
          <span className="absolute bottom-1 left-2 text-[9px] font-semibold text-plum-ink">Your location</span>
          <span className="absolute bottom-1 right-2 rounded bg-white/80 px-1 text-[8px] text-plum-ink/70">Sample data</span>
        </div>

        <div className="px-3 pb-4 pt-3">
          <p className="mb-2 text-xs font-semibold text-plum-ink">Choose your route</p>
          <div className="grid grid-cols-3 gap-2 text-[10px]">
            <div className="rounded-xl bg-teal-soft p-2 text-plum-ink">
              <div className="flex items-center gap-1 font-semibold">
                <ShieldTeal className="h-3 w-3" /> Safety
              </div>
              <div className="mt-1 text-xs font-bold">32 min</div>
            </div>
            <div className="rounded-xl bg-lavender-soft p-2 text-plum-ink">
              <div className="flex items-center gap-1 font-semibold">
                <Scales className="h-3 w-3" /> Balanced
              </div>
              <div className="mt-1 text-xs font-bold">25 min</div>
            </div>
            <div className="rounded-xl bg-coral-soft p-2 text-plum-ink">
              <div className="flex items-center gap-1 font-semibold">
                <Bolt className="h-3 w-3" /> Fastest
              </div>
              <div className="mt-1 text-xs font-bold">18 min</div>
            </div>
          </div>
          <button type="button" className="btn-primary mt-3 w-full">
            Start Navigation
          </button>
        </div>
      </div>
    </div>
  );
}
