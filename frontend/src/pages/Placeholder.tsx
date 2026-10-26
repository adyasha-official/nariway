import { Link } from "react-router-dom";
import { LogoMark, Wordmark } from "../components/Logo";

export default function Placeholder({ title, note }: { title: string; note: string }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-4 px-6 text-center">
      <LogoMark size={64} />
      <Wordmark className="text-3xl" />
      <h1 className="font-display text-2xl font-bold text-plum-deep">{title}</h1>
      <p className="text-sm text-plum-ink/75">{note}</p>
      <Link to="/" className="btn-primary">
        Back to home
      </Link>
    </main>
  );
}
