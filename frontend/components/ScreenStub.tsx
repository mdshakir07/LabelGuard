export default function ScreenStub({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-3 bg-neutral-50 p-8 text-center">
      <span className="rounded-full border border-neutral-300 bg-white px-3 py-1 text-xs font-medium uppercase tracking-wide text-neutral-500">
        Screen stub
      </span>
      <h1 className="text-2xl font-bold text-neutral-900">{title}</h1>
      <p className="max-w-md text-sm text-neutral-600">{description}</p>
    </main>
  );
}