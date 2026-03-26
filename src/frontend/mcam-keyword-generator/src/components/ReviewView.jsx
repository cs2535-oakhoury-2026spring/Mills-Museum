import { ChevronLeft, ChevronRight } from 'lucide-react'
import { ResultDisplay } from './figma/ResultDisplay'
import { buildCombinedExportText, downloadTextFile } from '../utils/keywordAdapters'

export default function ReviewView({
  results,
  resultIndex,
  setResultIndex,
  onUploadNew,
  onKeywordsChange,
}) {
  const current = results[resultIndex]

  const handleExportAll = () => {
    const text = buildCombinedExportText(results)
    downloadTextFile('mcam_keywords_export.txt', text)
  }

  const canGoPrev = resultIndex > 0
  const canGoNext = resultIndex < results.length - 1

  const errorCount = results.filter((r) => r.type === 'error').length

  return (
    <div className="flex flex-col gap-6">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800/60 bg-slate-900/40 px-6 py-4 shadow-lg">
        {/* Navigation */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setResultIndex((i) => Math.max(0, i - 1))}
            disabled={!canGoPrev}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 text-slate-200 ring-1 ring-slate-700 transition-all hover:bg-slate-700 hover:ring-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Previous image"
          >
            <ChevronLeft size={18} />
          </button>
          <div className="text-center">
            <span className="text-lg font-bold text-white">
              {results.length === 0 ? '—' : `${resultIndex + 1}`}
            </span>
            <span className="text-lg text-slate-500"> / {results.length}</span>
          </div>
          <button
            onClick={() =>
              setResultIndex((i) => Math.min(results.length - 1, i + 1))
            }
            disabled={!canGoNext}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 text-slate-200 ring-1 ring-slate-700 transition-all hover:bg-slate-700 hover:ring-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Next image"
          >
            <ChevronRight size={18} />
          </button>
        </div>

        {errorCount > 0 ? (
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/10 px-3 py-1 text-xs font-medium text-red-400 ring-1 ring-red-500/20">
              {errorCount} failed
            </span>
          </div>
        ) : null}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportAll}
            className="flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2.5 text-sm font-medium text-slate-200 ring-1 ring-slate-700 transition-all hover:bg-slate-700 hover:text-white"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Export all
          </button>
          <button
            onClick={onUploadNew}
            className="rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-amber-500/20 transition-all hover:from-amber-400 hover:to-orange-400"
          >
            Upload new
          </button>
        </div>
      </div>

      {/* Result Content */}
      {current?.type === 'error' ? (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-red-500/20 bg-red-500/5 px-8 py-12 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 text-red-400">
            <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-300">Could not process image</h3>
            <p className="mt-1 text-sm font-medium text-red-400">{current.file.name}</p>
            <p className="mt-2 text-sm text-red-400/70">{current.error}</p>
          </div>
          {current.previewUrl && (
            <img
              src={current.previewUrl}
              alt="Failed"
              className="mt-2 h-40 w-40 rounded-xl border border-red-500/20 object-contain"
            />
          )}
        </div>
      ) : current?.type === 'success' ? (
        <ResultDisplay
          keywords={current.keywords}
          imageSrc={current.previewUrl}
          onKeywordsChange={(next) => onKeywordsChange(resultIndex, next)}
          fileName={current.file.name}
        />
      ) : null}
    </div>
  )
}
