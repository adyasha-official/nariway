import { Group, NearbyHelp, PinSpark, ShieldCheck } from "./Icons";

const tiles = [
  {
    title: "Safer Routes",
    body: "Compare routes and choose the one that feels right for you",
    icon: <ShieldCheck />,
    bg: "bg-lavender-soft",
  },
  {
    title: "Travel Together",
    body: "Share your journey with trusted people. Opt-in, time-limited, revocable",
    icon: <Group />,
    bg: "bg-coral-soft",
  },
  {
    title: "Nearby Help",
    body: "Find police stations, hospitals and pharmacies close to you. Emergency: dial 112",
    icon: <NearbyHelp />,
    bg: "bg-teal-soft",
  },
  {
    title: "Community Reports",
    body: "Moderated observations from women, for women",
    icon: <PinSpark />,
    bg: "bg-lavender-soft",
  },
];

export default function FeatureTiles() {
  return (
    <ul id="features" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {tiles.map((t) => (
        <li key={t.title} className={`tile ${t.bg} flex flex-col items-center gap-2`}>
          <div className="grid h-16 place-items-center">{t.icon}</div>
          <h3 className="mt-1 text-base font-semibold text-plum-ink">{t.title}</h3>
          <p className="text-xs leading-relaxed text-plum-ink/70">{t.body}</p>
        </li>
      ))}
    </ul>
  );
}
