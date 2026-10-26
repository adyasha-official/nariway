import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import RouteModes from "../components/RouteModes";
import FeatureTiles from "../components/FeatureTiles";
import Evidence from "../components/Evidence";
import PhoneMockup from "../components/PhoneMockup";
import SkylineBanner from "../components/SkylineBanner";
import { TaglineCard } from "../components/BrandSection";

export default function Landing() {
  return (
    <>
      <div className="relative">
        <Navbar />
        <Hero />
      </div>
      <RouteModes />

      <section className="mx-auto max-w-[1100px] px-5 py-16 sm:px-8">
        <FeatureTiles />
      </section>

      <section className="bg-white/60 py-16">
        <div className="mx-auto grid max-w-[1100px] items-center gap-12 px-5 sm:px-8 md:grid-cols-2">
          <div>
            <h2 className="font-display text-[clamp(1.8rem,3vw,2.4rem)] font-bold text-plum-deep">Plan it. Compare it. Decide.</h2>
            <p className="mt-3 max-w-md text-[15px] leading-relaxed text-plum-ink/80">
              Enter where you are and where you are going. NariWay returns real route alternatives, shows travel time
              next to the safety evidence for each, and leaves the decision to you.
            </p>
          </div>
          <PhoneMockup />
        </div>
      </section>

      <Evidence />

      <section id="about" className="mx-auto max-w-[1100px] px-5 pb-6 sm:px-8">
        <TaglineCard />
      </section>
      <SkylineBanner />
    </>
  );
}
