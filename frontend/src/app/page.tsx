import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-24">
      <h1 className="text-3xl font-bold">Social Media Marketing Machine</h1>
      <p className="text-muted-foreground">AI-assisted campaign management for agencies.</p>
      <Link href="/dashboard" className="underline">
        Go to Dashboard
      </Link>
    </main>
  );
}
