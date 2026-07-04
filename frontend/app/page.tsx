import Link from 'next/link'
import { FlaskConical, BookOpen, Search, ArrowRight } from 'lucide-react'

const features = [
  {
    icon: FlaskConical,
    title: 'Experiments',
    description: 'Track and manage ML experiments with runs and metrics',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
  },
  {
    icon: BookOpen,
    title: 'Notebooks',
    description: 'Block-based research notebooks with code execution',
    color: 'text-green-600',
    bg: 'bg-green-50',
  },
  {
    icon: Search,
    title: 'Search',
    description: 'Semantic search across all your research assets',
    color: 'text-purple-600',
    bg: 'bg-purple-50',
  },
]

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 bg-muted/30">
      <div className="text-center animate-in max-w-lg">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary mb-6">
          <FlaskConical className="h-8 w-8 text-primary-foreground" />
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-foreground tracking-tight">
          ResearchOS
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          The research operating system for AI/ML teams
        </p>

        <div className="mt-8 flex items-center justify-center gap-3">
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center justify-center rounded-lg border border-border bg-card px-6 py-2.5 text-sm font-medium text-foreground hover:bg-accent transition-colors shadow-sm"
          >
            Get started
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      </div>

      <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl w-full">
        {features.map((feature) => {
          const Icon = feature.icon
          return (
            <div
              key={feature.title}
              className="rounded-xl bg-card p-5 border border-border shadow-sm hover:shadow-md transition-all"
            >
              <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg ${feature.bg} mb-3`}>
                <Icon className={`h-5 w-5 ${feature.color}`} />
              </div>
              <h3 className="font-semibold text-foreground">{feature.title}</h3>
              <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
                {feature.description}
              </p>
            </div>
          )
        })}
      </div>
    </main>
  )
}
