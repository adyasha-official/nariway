/** Decorative generic skyline of arches, domes and trees. Original shapes, not specific monuments. */
export default function SkylineBanner() {
  return (
    <footer className="relative mt-10 overflow-hidden bg-gradient-to-b from-plum to-plum-ink text-center text-white">
      <svg
        viewBox="0 0 1200 140"
        preserveAspectRatio="xMidYMax slice"
        className="absolute inset-x-0 top-0 h-32 w-full"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#f7a98f" stopOpacity=".95" />
            <stop offset="1" stopColor="#6B21AB" stopOpacity="0" />
          </linearGradient>
        </defs>
        <rect width="1200" height="140" fill="url(#sky)" />
        <g fill="#4A1580" opacity=".92">
          {/* arch gate */}
          <rect x="40" y="60" width="90" height="80" />
          <rect x="55" y="75" width="60" height="65" rx="30" fill="#6B21AB" />
          <rect x="35" y="52" width="100" height="10" />
          {/* trees */}
          <circle cx="190" cy="100" r="30" />
          <circle cx="600" cy="108" r="26" />
          {/* big dome building */}
          <rect x="260" y="82" width="200" height="58" />
          <path d="M300 82a60 60 0 0 1 120 0Z" />
          <rect x="358" y="30" width="4" height="22" />
          <rect x="262" y="60" width="14" height="80" />
          <rect x="444" y="60" width="14" height="80" />
          <path d="M262 60a7 7 0 0 1 14 0ZM444 60a7 7 0 0 1 14 0Z" />
          {/* minarets and domes */}
          <rect x="680" y="50" width="12" height="90" />
          <path d="M680 50a6 6 0 0 1 12 0Z" />
          <rect x="720" y="90" width="150" height="50" />
          <path d="M745 90a50 50 0 0 1 100 0Z" />
          <rect x="900" y="40" width="12" height="100" />
          <path d="M900 40a6 6 0 0 1 12 0Z" />
          <rect x="940" y="78" width="130" height="62" />
          <path d="M955 78a50 50 0 0 1 100 0Z" />
          <circle cx="1130" cy="104" r="28" />
        </g>
      </svg>
      <div className="relative px-6 pb-8 pt-32">
        <p className="font-display text-xl font-medium sm:text-2xl">For every woman.</p>
        <p className="font-display text-xl font-medium sm:text-2xl">For every destination.</p>
        <span className="mx-auto mt-3 block h-0.5 w-8 bg-white/70" />
        <p className="mx-auto mt-5 max-w-xl text-[11px] leading-relaxed text-white/70">
          NariWay provides information to support your decisions and cannot guarantee safety. In an emergency, call
          112. This is an early pilot and safety data coverage is limited.
        </p>
      </div>
    </footer>
  );
}
