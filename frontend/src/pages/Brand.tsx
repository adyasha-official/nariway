import { Link } from "react-router-dom";
import { IconVariations, Palette, TaglineCard } from "../components/BrandSection";
import { LogoMark, Wordmark } from "../components/Logo";

/** Brand reference: logo, palette and icon variations from the NariWay brand board. */
export default function Brand() {
  return (
    <main className="mx-auto max-w-[1100px] px-5 py-10 sm:px-8">
      <Link to="/" className="text-sm font-medium text-plum hover:underline">
        ← Back to home
      </Link>
      <div className="mt-6 flex items-center gap-5">
        <LogoMark size={110} />
        <div>
          <Wordmark className="text-6xl sm:text-7xl" />
          <p className="mt-2 font-display text-lg font-semibold text-plum-ink">Your safety. Your journey. Your way.</p>
          <p className="mt-1 text-sm text-plum-ink/75">Safety-first navigation, designed for women in India.</p>
        </div>
      </div>
      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <Palette />
        <IconVariations />
      </div>
      <div className="mt-6">
        <TaglineCard />
      </div>
    </main>
  );
}
