'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  FlaskConical,
  BookOpen,
  Search,
  ArrowRight,
  Sparkles,
  BarChart3,
  GitBranch,
} from 'lucide-react'
import { fadeInUp, staggerContainer, fadeIn, slideInRight } from '@/lib/hooks/use-motion'
import { TiltCard } from '@/components/ui/tilt-card'
import { ThemeToggle } from '@/components/theme-toggle'

const features = [
  {
    icon: FlaskConical,
    title: 'Experiments',
    description: 'Track and manage ML experiments with runs and metrics',
    gradient: 'from-blue-500 to-blue-600',
    bgLight: 'bg-blue-50',
    bgDark: 'dark:bg-blue-950/30',
  },
  {
    icon: BookOpen,
    title: 'Notebooks',
    description: 'Block-based research notebooks with code execution',
    gradient: 'from-emerald-500 to-emerald-600',
    bgLight: 'bg-emerald-50',
    bgDark: 'dark:bg-emerald-950/30',
  },
  {
    icon: Search,
    title: 'Search',
    description: 'Semantic search across all your research assets',
    gradient: 'from-purple-500 to-purple-600',
    bgLight: 'bg-purple-50',
    bgDark: 'dark:bg-purple-950/30',
  },
]

const stats = [
  { label: 'Experiments tracked', value: '10K+' },
  { label: 'Active researchers', value: '500+' },
  { label: 'Research hours saved', value: '40K+' },
]

export default function Home() {
  return (
    <main className="relative min-h-screen">
      {/* Grid overlay for hero area */}
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.03] dark:opacity-[0.05]" />

      {/* Nav bar */}
      <motion.header
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        className="relative z-10 flex items-center justify-between px-6 py-4 mx-auto max-w-6xl"
      >
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-sm">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="font-semibold tracking-tight">ResearchOS</span>
        </Link>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link
            href="/login"
            className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-all shadow-sm hover:shadow-md"
          >
            Get started
            <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
          </Link>
        </div>
      </motion.header>

      {/* Hero section */}
      <section className="relative z-10 flex flex-col items-center justify-center px-6 pt-24 pb-16 text-center">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="max-w-3xl"
        >
          {/* Badge */}
          <motion.div variants={fadeInUp} className="mb-6">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs font-medium text-muted-foreground">
              <Sparkles className="h-3 w-3 text-primary" />
              Where AI research meets velocity
            </span>
          </motion.div>

          {/* Title */}
          <motion.h1
            variants={fadeInUp}
            className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight leading-[1.1]"
          >
            <span className="text-gradient-primary">ResearchOS</span>
            <br />
            <span className="text-foreground">The OS for modern</span>
            <br />
            <span className="text-foreground">AI research teams</span>
          </motion.h1>

          {/* Description */}
          <motion.p
            variants={fadeInUp}
            className="mt-6 text-base sm:text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed"
          >
            A unified platform for managing experiments, notebooks, papers, and
            artifacts — powered by a research graph, semantic search, and
            multi-agent AI.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            variants={fadeInUp}
            className="mt-8 flex items-center justify-center gap-3"
          >
            <Link
              href="/signup"
              className="group relative inline-flex items-center justify-center rounded-xl bg-primary px-7 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all duration-300 hover:-translate-y-0.5"
            >
              Start building
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-xl border border-border bg-card px-7 py-3 text-sm font-medium text-foreground hover:bg-accent transition-all duration-200 shadow-sm"
            >
              Sign in
            </Link>
          </motion.div>
        </motion.div>

        {/* Social proof stats */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mt-16 flex items-center gap-8 sm:gap-12"
        >
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              variants={fadeInUp}
              className="text-center"
            >
              <div className="text-2xl font-bold tracking-tight text-foreground">
                {stat.value}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Features grid */}
      <section className="relative z-10 px-6 pb-24">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="mx-auto max-w-5xl"
        >
          <motion.div variants={fadeInUp} className="text-center mb-12">
            <h2 className="text-2xl font-semibold tracking-tight">
              Everything your research team needs
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              From experiment tracking to paper writing — one platform.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {features.map((feature, i) => {
              const Icon = feature.icon
              return (
                <motion.div key={feature.title} variants={fadeInUp}>
                  <TiltCard tiltDegree={6} scale={1.03} glare={false}>
                    <div className="group relative rounded-2xl border border-border bg-card p-6 h-full transition-all duration-300 hover:border-primary/20 hover:shadow-lg hover:shadow-primary/5">
                      {/* Gradient top border on hover */}
                      <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                      <div
                        className={`inline-flex items-center justify-center w-11 h-11 rounded-xl ${feature.bgLight} ${feature.bgDark} mb-4`}
                      >
                        <Icon className="h-5 w-5 text-foreground" />
                      </div>
                      <h3 className="font-semibold text-foreground text-base">
                        {feature.title}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </TiltCard>
                </motion.div>
              )
            })}
          </div>
        </motion.div>
      </section>

      {/* Bottom CTA */}
      <section className="relative z-10 px-6 pb-24">
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mx-auto max-w-2xl text-center"
        >
          <div className="rounded-2xl border border-border bg-card p-10 sm:p-14 relative overflow-hidden">
            {/* Subtle grid inside CTA */}
            <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.02]" />

            <div className="relative">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-4">
                <BarChart3 className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight">
                Ready to accelerate your research?
              </h2>
              <p className="mt-2 text-sm text-muted-foreground max-w-sm mx-auto">
                Join hundreds of research teams already using ResearchOS to ship
                faster.
              </p>
              <Link
                href="/signup"
                className="group mt-6 inline-flex items-center justify-center rounded-xl bg-primary px-7 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all duration-300 hover:-translate-y-0.5"
              >
                Get started free
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-8 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <GitBranch className="h-4 w-4" />
            <span>&copy; {new Date().getFullYear()} ResearchOS</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <Link href="/login" className="hover:text-foreground transition-colors">
              Sign in
            </Link>
            <Link href="/signup" className="hover:text-foreground transition-colors">
              Sign up
            </Link>
          </div>
        </div>
      </footer>
    </main>
  )
}
