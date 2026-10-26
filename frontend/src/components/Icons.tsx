import type { ReactNode } from "react";

type P = { className?: string };
const base = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
const Svg = ({ children, className = "h-5 w-5", viewBox = "0 0 24 24" }: { children: ReactNode; className?: string; viewBox?: string }) => (
  <svg viewBox={viewBox} className={className} aria-hidden="true" {...base}>
    {children}
  </svg>
);

export const ShieldCheck = ({ className = "h-12 w-12" }: P) => (
  <svg viewBox="0 0 48 52" className={className} aria-hidden="true">
    <defs>
      <linearGradient id="sh" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#7C3AED" />
        <stop offset="1" stopColor="#4A1580" />
      </linearGradient>
    </defs>
    <path d="M24 2 4 9v15c0 12 8 21 20 26 12-5 20-14 20-26V9L24 2Z" fill="url(#sh)" />
    <path d="m15 26 7 7 12-14" fill="none" stroke="#fff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Group = ({ className = "h-12 w-14" }: P) => (
  <svg viewBox="0 0 64 52" className={className} aria-hidden="true" fill="#FF7F6E">
    <circle cx="32" cy="14" r="9" />
    <path d="M14 46c0-10 8-17 18-17s18 7 18 17H14Z" />
    <circle cx="11" cy="22" r="6" opacity=".8" />
    <path d="M0 44c0-8 5-13 11-13 3 0 5 1 7 2-3 3-4 7-4 11H0Z" opacity=".8" />
    <circle cx="53" cy="22" r="6" opacity=".8" />
    <path d="M64 44c0-8-5-13-11-13-3 0-5 1-7 2 3 3 4 7 4 11h14Z" opacity=".8" />
  </svg>
);

export const NearbyHelp = ({ className = "h-14 w-14" }: P) => (
  <svg viewBox="0 0 56 56" className={className} aria-hidden="true">
    <circle cx="28" cy="28" r="26" fill="#14B8A6" />
    <path d="M28 12v32M12 28h32" stroke="#fff" strokeWidth="7" strokeLinecap="round" />
  </svg>
);

export const PinSpark = ({ className = "h-12 w-12" }: P) => (
  <svg viewBox="0 0 52 56" className={className} aria-hidden="true">
    <defs>
      <linearGradient id="ps" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#6B21AB" />
        <stop offset="1" stopColor="#8B3FD1" />
      </linearGradient>
    </defs>
    <path d="M24 4C14 4 6 12 6 22c0 14 18 30 18 30s18-16 18-30C42 12 34 4 24 4Z" fill="url(#ps)" />
    <path d="m24 14 3 6 6 1-5 5 1 7-5-3-5 3 1-7-5-5 6-1Z" fill="#fff" />
    <path d="M43 4l1.6 4 4 1.6-4 1.6L43 15l-1.6-3.8-4-1.6 4-1.6Z" fill="#6B21AB" />
  </svg>
);

export const ShieldTeal = ({ className = "h-7 w-7" }: P) => (
  <svg viewBox="0 0 32 36" className={className} aria-hidden="true">
    <path d="M16 2 3 7v10c0 8 5.5 14 13 17 7.5-3 13-9 13-17V7L16 2Z" fill="#14B8A6" />
    <path d="m10 18 4.5 4.5L23 13" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export const Scales = ({ className = "h-6 w-6" }: P) => (
  <Svg className={className}>
    <path d="M12 3v18M7 21h10M5 7h14" />
    <path d="m5 7-3 7a4 4 0 0 0 6 0L5 7Zm14 0-3 7a4 4 0 0 0 6 0l-3-7Z" />
  </Svg>
);

export const Bolt = ({ className = "h-6 w-6" }: P) => (
  <svg viewBox="0 0 24 24" className={className} aria-hidden="true" fill="#FF7F6E">
    <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" />
  </svg>
);

export const Pin = ({ className = "h-4 w-4" }: P) => (
  <Svg className={className}>
    <path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z" />
    <circle cx="12" cy="10" r="2.4" />
  </Svg>
);

export const Swap = ({ className = "h-4 w-4" }: P) => (
  <Svg className={className}>
    <path d="M8 4v16m0 0-3-3m3 3 3-3M16 20V4m0 0-3 3m3-3 3 3" />
  </Svg>
);

export const Walk = ({ className = "h-5 w-5" }: P) => (
  <Svg className={className}>
    <circle cx="13" cy="4.5" r="1.8" />
    <path d="m9 21 2.5-6-2-3 1.5-4 3 2 3 1M13 8l-1 4m1.5 3L16 21" />
  </Svg>
);

export const Bus = ({ className = "h-5 w-5" }: P) => (
  <Svg className={className}>
    <rect x="4" y="3" width="16" height="15" rx="3" />
    <path d="M4 11h16M8 21v-3m8 3v-3" />
    <circle cx="8.5" cy="14.5" r=".6" />
    <circle cx="15.5" cy="14.5" r=".6" />
  </Svg>
);

export const Bike = ({ className = "h-5 w-5" }: P) => (
  <Svg className={className}>
    <circle cx="5.5" cy="16.5" r="3.5" />
    <circle cx="18.5" cy="16.5" r="3.5" />
    <path d="M5.5 16.5 9 9h5l4.5 7.5M9 9 12 16.5M13 6h3" />
  </Svg>
);

export const Car = ({ className = "h-5 w-5" }: P) => (
  <Svg className={className}>
    <path d="M5 16V11l2-5h10l2 5v5M3 16h18v3H3zM6 11h12" />
    <circle cx="7.5" cy="14" r=".6" />
    <circle cx="16.5" cy="14" r=".6" />
  </Svg>
);

export const Person = ({ className = "h-5 w-5" }: P) => (
  <Svg className={className}>
    <circle cx="12" cy="8" r="3.5" />
    <path d="M5 21c0-4 3-7 7-7s7 3 7 7" />
  </Svg>
);

export const Menu = ({ className = "h-5 w-5" }: P) => (
  <Svg className={className}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </Svg>
);

export const Bell = ({ className = "h-5 w-5" }: P) => (
  <Svg className={className}>
    <path d="M6 17V11a6 6 0 1 1 12 0v6l1.5 2h-15L6 17ZM10 21h4" />
  </Svg>
);

export const Arrow = ({ className = "h-4 w-4" }: P) => (
  <Svg className={className}>
    <path d="M5 12h14m-6-6 6 6-6 6" />
  </Svg>
);

export const Play = ({ className = "h-4 w-4" }: P) => (
  <svg viewBox="0 0 24 24" className={className} aria-hidden="true" fill="currentColor">
    <path d="M8 5v14l11-7L8 5Z" />
  </svg>
);
