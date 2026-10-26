import { Link } from "react-router-dom";
import { Arrow, Play } from "./Icons";

/**
 * Full-bleed dusk hero. The photograph lives at frontend/public/hero.jpg.
 * It is currently cropped from the brand board; replace it with your original
 * high-resolution image (portrait subject on the right, sky behind) and nothing else changes.
 */
export default function Hero() {
  return (
    <section className="relative isolate overflow-hidden bg-gradient-to-br from-[#e6d3fa] via-[#f4cddd] to-[#fbd8cc]">
      {/* soft blurred skyline behind the headline */}
      <svg
        viewBox="0 0 800 400"
        preserveAspectRatio="xMinYMax slice"
        className="absolute inset-y-0 left-0 -z-10 h-full w-[70%] opacity-35 blur-[6px]"
        aria-hidden="true"
      >
        <g fill="#c9a6dc">
          <rect x="40" y="190" width="46" height="210" />
          <rect x="100" y="140" width="36" height="260" />
          <rect x="150" y="215" width="58" height="185" />
          <rect x="230" y="165" width="42" height="235" />
          <rect x="300" y="235" width="64" height="165" />
          <rect x="380" y="180" width="40" height="220" />
        </g>
        <g fill="#b48bd0" opacity=".7">
          <rect x="70" y="260" width="54" height="140" />
          <rect x="190" y="250" width="40" height="150" />
          <rect x="270" y="280" width="60" height="120" />
        </g>
      </svg>

      {/* photograph, fading into the sky on its left edge */}
      <img
        src="/hero.jpg"
        alt="A young woman checking her route on her phone at dusk, city skyline behind her"
        className="absolute inset-y-0 right-0 -z-10 hidden h-full w-[56%] object-cover object-[50%_20%] md:block [mask-image:linear-gradient(to_right,transparent,#000_28%)]"
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).style.display = "none";
        }}
      />

      <div className="mx-auto grid min-h-[600px] max-w-[1240px] items-center px-5 pb-16 pt-32 sm:px-8 md:min-h-[640px]">
        <div className="max-w-[520px]">
          <h1 className="font-display text-[clamp(2.9rem,6vw,4.6rem)] font-bold leading-[1.04] tracking-tight text-plum-deep">
            Move freely.
            <br />
            <span className="text-coral">Feel safer.</span>
          </h1>
          <p className="mt-6 max-w-[430px] text-[16px] leading-relaxed text-plum-ink">
            NariWay helps you compare routes, stay connected with trusted people, and travel with greater
            confidence, in every journey you plan.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/navigate" className="btn-primary !px-7 !py-3.5">
              Start Your Journey <Arrow />
            </Link>
            <a href="#how-it-works" className="btn-outline !px-7 !py-3.5">
              <Play className="h-3.5 w-3.5" /> See How It Works
            </a>
          </div>
          <p className="mt-5 max-w-[430px] text-xs text-plum-ink/60">
            No route can be guaranteed safe. NariWay shows what is known and what is not, and the choice stays yours.
          </p>
        </div>
      </div>
    </section>
  );
}
