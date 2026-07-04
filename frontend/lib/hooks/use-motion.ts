'use client'

import { type Variants } from 'framer-motion'

/**
 * Framer Motion variant presets for consistent animations across the app.
 * All use the Geist-approved ease curve: cubic-bezier(0.16, 1, 0.3, 1)
 */

export const easeOutExpo = [0.16, 1, 0.3, 1] as const

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3, ease: easeOutExpo } },
}

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: easeOutExpo },
  },
}

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: easeOutExpo },
  },
}

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.2, ease: easeOutExpo },
  },
}

export const slideInRight: Variants = {
  hidden: { opacity: 0, x: 16 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.3, ease: easeOutExpo },
  },
}

export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -16 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.3, ease: easeOutExpo },
  },
}

/**
 * Stagger children animations.
 * Usage: <motion.div variants={staggerContainer} initial="hidden" animate="visible">
 *          <motion.div variants={fadeInUp} />
 *          <motion.div variants={fadeInUp} />
 *        </motion.div>
 */
export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
}

/**
 * Page transition (route changes).
 * Wraps page content in AnimatePresence + this variant.
 */
export const pageTransition: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: easeOutExpo },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: { duration: 0.15, ease: easeOutExpo },
  },
}

/**
 * Sidebar expand/collapse animation.
 */
export const sidebarAnimation: Variants = {
  expanded: { width: 240, transition: { duration: 0.2, ease: easeOutExpo } },
  collapsed: { width: 56, transition: { duration: 0.2, ease: easeOutExpo } },
}

/**
 * Modal backdrop + content animations.
 */
export const modalBackdrop: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
}

export const modalContent: Variants = {
  hidden: { opacity: 0, scale: 0.95, y: 10 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: 0.2, ease: easeOutExpo },
  },
}
