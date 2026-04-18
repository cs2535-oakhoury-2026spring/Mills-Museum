/**
 * Full-width processing card: image preview, optional staggered keyword chips,
 * streamed AI description, and an animated progress bar. Used by `App` during
 * batch inference.
 */
import { motion } from 'motion/react'
import { useEffect, useState } from 'react'

/**
 * @param {object} props
 * @param {number} props.progress 0–100; drives bar width and "analyzing" vs "keywords" copy.
 * @param {string} [props.imageSrc] Object URL or URL string for the current file preview.
 * @param {Array<{ text: string, confidence: number }>} props.keywords Keyword chips revealed when `progress === 100`.
 * @param {string} [props.statusLabel] e.g. "Processing image 2 of 5".
 * @param {string} [props.description] Streamed AI description text (builds up token by token).
 * @param {boolean} [props.descriptionDone] True once the description stream has finished.
 * @param {string} [props.processingStatus] Backend status message (e.g. "Retrieving keywords...").
 */
export function ProcessingDisplay({
  progress,
  imageSrc,
  keywords,
  statusLabel,
  description,
  descriptionDone,
  processingStatus,
}) {
  const [visibleKeywords, setVisibleKeywords] = useState([])

  // While work is in flight, hide chips. At 100%, append keywords one-by-one for a short staggered entrance.
  useEffect(() => {
    if (progress < 100) {
      setVisibleKeywords([])
      return
    }
    setVisibleKeywords([])
    keywords.forEach((keyword, index) => {
      setTimeout(() => {
        setVisibleKeywords((prev) => [...prev, keyword])
      }, index * 200)
    })
  }, [progress, keywords])

  return (
    <div className="w-full max-w-4xl">
      {/* Page title + optional batch position label from parent */}
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-mcam-blue">Processing</h2>
        {statusLabel ? (
          <p className="mt-1 text-xs text-mcam-muted">{statusLabel}</p>
        ) : null}
      </div>

      <div className="rounded-lg border-2 border-mcam-navy/20 bg-white p-8 shadow-sm">
        <div className="mb-6 flex flex-col gap-8 sm:flex-row">
          {/* Current file thumbnail (object URL from parent while predicting) */}
          <div className="relative mx-auto h-64 w-full max-w-64 flex-shrink-0 overflow-hidden rounded border border-mcam-navy/15 bg-mcam-surface sm:mx-0">
            {imageSrc ? (
              <img
                src={imageSrc}
                alt="Preview of the image being processed"
                className="absolute inset-0 box-border h-full w-full max-h-full max-w-full object-contain object-center p-2"
              />
            ) : (
              <span className="absolute inset-0 flex items-center justify-center px-4 text-center text-xs text-mcam-muted">
                No preview
              </span>
            )}
          </div>

          {/* Status copy + description + keyword chips */}
          <div className="min-w-0 flex-1">
            {progress < 100 ? (
              <div className="mb-4">
                <p className="text-sm font-medium text-mcam-navy">
                  {processingStatus || 'Analyzing image\u2026'}
                </p>
                <p className="mt-1 text-xs text-mcam-muted">
                  Calling the keyword model — this may take a moment per file.
                </p>
              </div>
            ) : (
              <div className="mb-4">
                <p className="text-sm font-medium text-mcam-navy">Keywords</p>
                <p className="mt-1 text-xs text-mcam-muted">
                  {visibleKeywords.length} of {keywords.length} keywords shown
                </p>
              </div>
            )}

            {/* Streamed AI description */}
            {description ? (
              <div className="mb-4 rounded border border-mcam-navy/10 bg-mcam-surface/50 p-3">
                <p className="mb-1 text-[11px] font-semibold tracking-wide text-mcam-blue uppercase">
                  AI Description
                </p>
                <p className="text-xs leading-relaxed text-mcam-navy/80">
                  {description}
                  {!descriptionDone ? (
                    <span className="ml-0.5 inline-block w-1.5 animate-pulse text-mcam-blue">|</span>
                  ) : null}
                </p>
              </div>
            ) : null}

            {/* Motion-wrapped pills; empty while predicting or when parent passes no `keywords` */}
            <div className="flex flex-wrap gap-2">
              {visibleKeywords.map((keyword, index) => (
                <motion.div
                  key={`${keyword.text}-${index}`}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <span className="inline-flex items-center gap-2 rounded border border-[#2f5a94]/50 bg-[#3b6db5] px-3 py-1.5 text-xs font-medium !text-white shadow-sm">
                    {keyword.text}
                    <span className="rounded border border-white/30 bg-white/15 px-1 py-px text-[10px] font-semibold tabular-nums text-white">
                      {keyword.confidence}%
                    </span>
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        {/* Overall batch fraction complete (each file advances `progress` in App) */}
        <div className="h-1.5 w-full overflow-hidden rounded-full border border-mcam-navy/10 bg-mcam-surface">
          <div
            className="h-full bg-mcam-blue transition-[width] duration-300 ease-out"
            style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
          />
        </div>

        {/* Numeric hint while still running; hides at 100% when keyword header shows counts */}
        {progress < 100 ? (
          <div className="mt-2 text-right text-xs text-mcam-muted">
            {Math.round(progress)}% complete
          </div>
        ) : null}
      </div>
    </div>
  )
}
