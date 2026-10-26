const points = [
  { h: "See the evidence", p: "Every route lists what it is based on: lighting, road type, open places nearby and recent reports, with where each came from and how fresh it is." },
  { h: "Unknown stays unknown", p: "If we have no information about a street, we say so. Missing data is never treated as a sign that a street is safe." },
  { h: "Honest about limits", p: "Assessments are a decision aid built from available evidence. They are not a prediction, and no route can be guaranteed safe." },
];

export default function Evidence() {
  return (
    <section id="safety-tips" className="mx-auto max-w-[1100px] px-5 py-16 sm:px-8">
      <h2 className="text-center font-display text-[clamp(1.7rem,3vw,2.3rem)] font-bold text-plum-deep">Safety you can see into</h2>
      <p className="mx-auto mt-2 max-w-xl text-center text-sm text-plum-ink/70">
        A score you cannot question can create false confidence. NariWay shows its working.
      </p>
      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {points.map((x) => (
          <article key={x.h} className="rounded-2xl bg-white/80 p-6 shadow-card">
            <h3 className="font-semibold text-plum-ink">{x.h}</h3>
            <p className="mt-2 text-[13px] leading-relaxed text-plum-ink/75">{x.p}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
