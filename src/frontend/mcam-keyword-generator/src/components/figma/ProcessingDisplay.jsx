import { motion } from 'motion/react'
import { useEffect, useState } from 'react'

export function ProcessingDisplay({ progress, imageSrc, keywords, statusLabel }) {
  const [visibleKeywords, setVisibleKeywords] = useState([])

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
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-mcam-blue">Processing</h2>
        {statusLabel ? (
          <p className="mt-1 text-xs text-mcam-muted">{statusLabel}</p>
        ) : null}
      </div>

      <div className="rounded-lg border-2 border-mcam-navy/20 bg-white p-8 shadow-sm">
        <div className="mb-6 flex flex-col gap-8 sm:flex-row">
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

          <div className="min-w-0 flex-1">
            {progress < 100 ? (
              <div className="mb-4">
                <p className="text-sm font-medium text-mcam-navy">Analyzing image…</p>
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

        <div className="h-1.5 w-full overflow-hidden rounded-full border border-mcam-navy/10 bg-mcam-surface">
          <motion.div
            className="h-full bg-mcam-navy"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {progress < 100 ? (
          <div className="mt-2 text-right text-xs text-mcam-muted">
            {Math.round(progress)}% complete
          </div>
        ) : null}
      </div>
    </div>
  )
}
