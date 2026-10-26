import { Link } from "react-router-dom";
import { LogoMark, Wordmark } from "./Logo";

const links = [
  { label: "Home", href: "/" },
  { label: "Features", href: "/#features" },
  { label: "How It Works", href: "/#how-it-works" },
  { label: "Safety Tips", href: "/#safety-tips" },
  { label: "About", href: "/#about" },
];

/** Sits on top of the hero photo, exactly like the brand board. */
export default function Navbar() {
  return (
    <header className="absolute inset-x-0 top-0 z-30">
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-5 py-5 sm:px-8">
        <Link to="/" className="flex items-center gap-2.5" aria-label="NariWay home">
          <LogoMark size={36} />
          <div>
            <Wordmark className="text-[26px]" />
            <p className="mt-0.5 hidden text-[8.5px] font-medium tracking-wide text-plum-ink/70 sm:block">
              Your safety. Your journey. Your way.
            </p>
          </div>
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-9 text-[13.5px] font-medium text-plum-ink md:flex">
          {links.map((l) => (
            <a key={l.label} href={l.href} className="transition hover:text-plum">
              {l.label}
            </a>
          ))}
        </nav>

        <Link to="/navigate" className="btn-primary !px-6 !py-2.5">
          Get Started
        </Link>
      </div>
    </header>
  );
}
