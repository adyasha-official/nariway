import { useId } from "react";

type MarkProps = {
  size?: number;
  /** "color" is the full-colour brand mark. "mono" draws it in two tones (paper + ink) for app icons. */
  variant?: "color" | "mono";
  paper?: string;
  ink?: string;
  className?: string;
};

const PIN = "M50 2C24 2 4 22 4 47c0 23 24 45 46 69 22-24 46-46 46-69C96 22 76 2 50 2Z";
const HAIR =
  "M52 0C24 0 0 22 0 50c0 20 20 36 36 50-6-16-2-30 6-38 8-8 4-18 2-26-2-10 2-22 12-28-2-3-3-6-4-8Z";
const FACE =
  "M54 10c10 2 14 12 13 21 0 3 3 7 5 9-1 2-4 2-4 3 1 2 1 3-1 4 1 2 0 4-1 5 1 4-2 7-6 8v10H40l2-30c0-16 4-28 12-30Z";
const WEDGE = "M100 44C72 48 60 58 64 72c4 14-6 30-20 48h66V44Z";
const ROAD =
  "M14 100c20-4 38-12 40-22 2-10-12-12-8-20 4-8 24-2 52-12v8c-24 8-36 6-36 14 0 14-14 30-32 44H14Z";
const ROAD_LINE = "M26 106c16-8 32-20 30-30-2-10-12-10-6-16 6-6 26-2 46-10";
const SPARK = "M78 14l2.6 6.4 6.4 2.6-6.4 2.6L78 32l-2.6-6.4-6.4-2.6 6.4-2.6Z";

/** Original NariWay mark: a map pin holding a woman's profile and a winding road. */
export function LogoMark({ size = 72, variant = "color", paper = "#FFFFFF", ink = "#6B21AB", className }: MarkProps) {
  const uid = useId().replace(/:/g, "");
  const mono = variant === "mono";
  return (
    <svg
      width={size}
      height={(size * 118) / 100}
      viewBox="0 0 100 118"
      className={className}
      role="img"
      aria-label="NariWay logo"
    >
      <defs>
        <clipPath id={`${uid}-pin`}>
          <path d={PIN} />
        </clipPath>
        <linearGradient id={`${uid}-sky`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FF8F7E" />
          <stop offset="1" stopColor="#FFD2C2" />
        </linearGradient>
        <linearGradient id={`${uid}-hair`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#4A1580" />
          <stop offset="1" stopColor="#7A2CC0" />
        </linearGradient>
        <linearGradient id={`${uid}-teal`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#1FC9B5" />
          <stop offset="1" stopColor="#0E8F82" />
        </linearGradient>
      </defs>
      <g clipPath={`url(#${uid}-pin)`}>
        <rect width="100" height="118" fill={mono ? paper : `url(#${uid}-sky)`} />
        {!mono && <path d={WEDGE} fill={`url(#${uid}-teal)`} />}
        <path d={FACE} fill={mono ? paper : "#FFF3EE"} stroke={mono ? ink : "none"} strokeWidth="1.6" />
        <path d={HAIR} fill={mono ? ink : `url(#${uid}-hair)`} />
        {!mono && <path d="M14 40c4-14 14-22 26-26" stroke="#9B5BDA" strokeWidth="1.4" fill="none" opacity=".6" />}
        <path d={ROAD} fill={mono ? ink : "#5B1A9A"} />
        <path
          d={ROAD_LINE}
          fill="none"
          stroke={mono ? paper : "#FFFFFF"}
          strokeWidth="1.6"
          strokeDasharray="4 3.5"
          strokeLinecap="round"
        />
      </g>
      <path d={SPARK} fill={mono ? ink : "#FFFFFF"} />
    </svg>
  );
}

export function Wordmark({ className = "", tone = "default" }: { className?: string; tone?: "default" | "light" }) {
  return (
    <span className={`font-display font-bold leading-none tracking-tight ${className}`}>
      <span className={tone === "light" ? "text-white" : "text-plum-deep"}>Nari</span>
      <span className="bg-gradient-to-r from-coral from-35% to-teal bg-clip-text text-transparent">Way</span>
    </span>
  );
}
