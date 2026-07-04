import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-gray-50 to-white">
      <h1 className="text-5xl font-bold text-gray-900">ResearchOS</h1>
      <p className="mt-4 text-xl text-gray-600 max-w-md text-center">
        The research operating system for AI/ML teams
      </p>

      <div className="mt-10 flex gap-4">
        <Link
          href="/login"
          className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          Sign in
        </Link>
        <Link
          href="/signup"
          className="rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Get started
        </Link>
      </div>

      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl">
        <div className="text-center">
          <div className="text-3xl mb-2">🧪</div>
          <h3 className="font-semibold text-gray-900">Experiments</h3>
          <p className="text-sm text-gray-500 mt-1">Track and manage ML experiments</p>
        </div>
        <div className="text-center">
          <div className="text-3xl mb-2">📓</div>
          <h3 className="font-semibold text-gray-900">Notebooks</h3>
          <p className="text-sm text-gray-500 mt-1">Block-based research notebooks</p>
        </div>
        <div className="text-center">
          <div className="text-3xl mb-2">🔍</div>
          <h3 className="font-semibold text-gray-900">Search</h3>
          <p className="text-sm text-gray-500 mt-1">Semantic search across all research</p>
        </div>
      </div>
    </main>
  )
}
