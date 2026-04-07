import { ChevronLeft, ChevronRight } from 'lucide-react'
import { ResultDisplay } from './figma/ResultDisplay'
import { buildCombinedExportText, downloadTextFile } from '../utils/keywordAdapters'
import { reviewActionButtonLg } from '../utils/reviewActionStyles'

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
    <div className="mx-auto flex w-full max-w-6xl min-w-0 flex-col gap-6">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border-2 border-mcam-navy/20 bg-white px-6 py-4 shadow-sm">
        {/* Navigation */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setResultIndex((i) => Math.max(0, i - 1))}
            disabled={!canGoPrev}
            className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-mcam-navy/20 bg-mcam-surface text-mcam-navy transition-all hover:border-mcam-blue hover:bg-mcam-blue-light hover:text-mcam-blue disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:bg-white disabled:text-mcam-muted"
            aria-label="Previous image"
          >
            <ChevronLeft size={18} />
          </button>
          <div className="text-center">
            <span className="text-lg font-bold text-mcam-navy">
              {results.length === 0 ? '—' : `${resultIndex + 1}`}
            </span>
            <span className="text-lg text-mcam-muted"> / {results.length}</span>
          </div>
          <button
            onClick={() =>
              setResultIndex((i) => Math.min(results.length - 1, i + 1))
            }
            disabled={!canGoNext}
            className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-mcam-navy/20 bg-mcam-surface text-mcam-navy transition-all hover:border-mcam-blue hover:bg-mcam-blue-light hover:text-mcam-blue disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:bg-white disabled:text-mcam-muted"
            aria-label="Next image"
          >
            <ChevronRight size={18} />
          </button>
        </div>

        {errorCount > 0 ? (
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-800 ring-1 ring-red-200">
              {errorCount} failed
            </span>
          </div>
        ) : null}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExportAll}
            className={reviewActionButtonLg}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Export all
          </button>
          <button
            type="button"
            onClick={onUploadNew}
            className={reviewActionButtonLg}
          >
            Upload new
          </button>
        </div>
      </div>

      {/* Result Content */}
      {current?.type === 'error' ? (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-red-200 bg-red-50/80 px-8 py-12 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-red-600">
            <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-900">Could not process image</h3>
            <p className="mt-1 text-sm font-medium text-red-800">{current.file.name}</p>
            <p className="mt-2 text-sm text-red-800">{current.error}</p>
          </div>
          {current.previewUrl && (
            <div className="relative mt-2 h-40 w-40 overflow-hidden rounded-xl border border-red-200 bg-red-50/50">
              <img
                src={current.previewUrl}
                alt="Failed"
                className="absolute inset-0 box-border h-full w-full max-h-full max-w-full object-contain object-center p-2"
              />
            </div>
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
