/**
 * Shared button styles for the review flow.
 *
 * We keep these as constants (instead of repeating long class strings) so the
 * primary actions look consistent across screens and are easy to tweak in one
 * place. Large vs small variants differ mainly in padding + font sizing.
 */
export const reviewActionButtonLg =
  'inline-flex items-center justify-center gap-2 rounded-xl border border-[#2f5a94]/60 bg-[#3b6db5] px-4 py-2.5 text-sm font-semibold !text-white shadow-md transition-colors hover:brightness-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#3b6db5] disabled:cursor-not-allowed disabled:border-[#c5cedd] disabled:bg-[#e8ecf2] disabled:!text-[#3d4d66] disabled:shadow-none'

/** Smaller variant for compact actions (copy/export within a panel). */
export const reviewActionButtonSm =
  'inline-flex items-center justify-center gap-1.5 rounded-md border border-[#2f5a94]/60 bg-[#3b6db5] px-3 py-1.5 text-xs font-semibold !text-white shadow-sm transition-colors hover:brightness-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#3b6db5] disabled:cursor-not-allowed disabled:border-[#c5cedd] disabled:bg-[#e8ecf2] disabled:!text-[#3d4d66] disabled:shadow-none'
