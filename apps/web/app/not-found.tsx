import Link from "next/link";

export default function NotFound() {
  return (
    <main className="h-dvh w-screen grid place-items-center bg-bg text-text-dim">
      <div className="text-center px-8 max-w-md">
        <p className="ewl-num text-5xl font-bold text-accent">404</p>
        <h1 className="mt-3 text-lg font-semibold text-text">Page not found</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          That route doesn’t exist. The lab lives at the workspace root.
        </p>
        <Link
          href="/"
          className="inline-block mt-5 px-4 py-2 rounded-md bg-accent text-[#062018] text-[13px] font-semibold hover:bg-accent-bright transition-colors"
        >
          Back to the lab
        </Link>
      </div>
    </main>
  );
}
