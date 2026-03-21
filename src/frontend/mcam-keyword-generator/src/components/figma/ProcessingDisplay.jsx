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
        <h2 className="text-sm font-medium text-blue-400">Processing</h2>
        {statusLabel ? (
          <p className="mt-1 text-xs text-slate-500">{statusLabel}</p>
        ) : null}
      </div>

      <div className="rounded-lg bg-slate-800 p-8">
        <div className="mb-6 flex flex-col gap-8 sm:flex-row">
          <div className="mx-auto flex aspect-square w-full max-w-64 flex-shrink-0 items-center justify-center overflow-hidden rounded bg-slate-700 sm:mx-0">
            {imageSrc ? (
              <img
                src={imageSrc}
                alt="Preview of the image being processed"
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="px-4 text-center text-xs text-slate-500">No preview</span>
            )}
          </div>

          <div className="min-w-0 flex-1">
            {progress < 100 ? (
              <div className="mb-4">
                <p className="text-sm font-medium text-slate-300">Analyzing image…</p>
                <p className="mt-1 text-xs text-slate-500">
                  Calling the keyword model — this may take a moment per file.
                </p>
              </div>
            ) : (
              <div className="mb-4">
                <p className="text-sm font-medium text-slate-300">Keywords</p>
                <p className="mt-1 text-xs text-slate-500">
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
                  <span className="inline-flex items-center gap-2 rounded bg-amber-500 px-3 py-1.5 text-xs font-medium text-slate-900">
                    {keyword.text}
                    <span className="text-[10px] opacity-70">{keyword.confidence}%</span>
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        </div>

        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-700">
          <motion.div
            className="h-full bg-blue-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>

        {progress < 100 ? (
          <div className="mt-2 text-right text-xs text-slate-500">
            {Math.round(progress)}% complete
          </div>
        ) : null}
      </div>
    </div>
  )
}
