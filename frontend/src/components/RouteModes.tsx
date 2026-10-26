import { Bolt, Scales, ShieldTeal } from "./Icons";

const modes = [
  {
    key: "safety",
    title: "Safety First",
    body: "Favours routes with more verified safety information, like lighting, main streets and open places.",
    chip: "May take longer",
    chipClass: "bg-teal/15 text-teal-900",
    cardClass: "bg-teal-soft border-teal/20",
    icon: <ShieldTeal className="h-10 w-10" />,
  },
  {
    key: "balanced",
    title: "Balanced",
    body: "A good mix of available safety information and travel time.",
    chip: "Recommended",
    chipClass: "bg-lavender text-plum-deep",
    cardClass: "bg-lavender-soft border-plum/15",
    icon: (
      <span className="grid h-10 w-10 place-items-center rounded-full bg-lavender text-plum">
        <Scales />
      </span>
    ),
  },
  {
    key: "fastest",
    title: "Fastest",
    body: "Gets you there sooner, and still shows known hazards and warnings along the way.",
    chip: "Shortest time",
    chipClass: "bg-coral/15 text-[#c2412f]",
    cardClass: "bg-coral-soft border-coral/25",
    icon: (
      <span className="grid h-10 w-10 place-items-center rounded-full bg-coral/15">
        <Bolt />
      </span>
    ),
  },
];

export default function RouteModes() {
  return (
    <section id="how-it-works" className="bg-white px-5 pb-16 pt-14 text-center sm:px-8">
      <h2 className="font-display text-[clamp(1.9rem,3.4vw,2.6rem)] font-bold text-plum-deep">Three Routes. You Choose.</h2>
      <p className="mt-2 text-sm text-plum-ink/75">Because every journey is different, and you know yours best.</p>
      <div className="mx-auto mt-9 grid max-w-[1100px] gap-5 text-left md:grid-cols-3">
        {modes.map((m) => (
          <article key={m.key} className={`flex gap-4 rounded-2xl border p-6 ${m.cardClass}`}>
            <div className="shrink-0 pt-0.5">{m.icon}</div>
            <div className="flex flex-col gap-2">
              <h3 className="text-[17px] font-semibold text-plum-ink">{m.title}</h3>
              <p className="text-[13px] leading-relaxed text-plum-ink/75">{m.body}</p>
              <span className={`mt-2 w-fit rounded-full px-4 py-1.5 text-xs font-semibold ${m.chipClass}`}>{m.chip}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
