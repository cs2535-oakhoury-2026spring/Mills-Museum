import { ChevronLeft, ChevronRight } from 'lucide-react'
import { ResultDisplay } from './ResultDisplay'
import {
  buildCombinedExportCsv,
  buildCombinedExportText,
  downloadTextFile,
} from '../utils/keywordAdapters'
import { reviewActionButtonLg } from '../utils/reviewActionStyles'

/**
 * Batch review "shell" for results.
 *
 * This component intentionally keeps no internal state for the review data:
 * the parent owns `results` and `resultIndex`. Here we focus on:
 * - navigation between results
 * - batch actions (export all, upload new)
 * - routing to either an error panel or the per-image `ResultDisplay`
 */
export default function ReviewView({
  results,
  resultIndex,
  setResultIndex,
  onUploadNew,
  onKeywordsChange,
}) {
  // Current item is derived from props so the view stays in sync with parent state.
  const current = results[resultIndex]

  const handleExportAll = () => {
    // Export uses shared adapters so UI + exports follow the same inclusion rules.
    const text = buildCombinedExportText(results)
    downloadTextFile('mcam_keywords_export.txt', text)
  }

  const handleExportCsv = () => {
    const csv = buildCombinedExportCsv(results)
    downloadTextFile('mcam_keywords_export.csv', csv)
  }

  // Clamp navigation via derived booleans and guarded index updates.
  const canGoPrev = resultIndex > 0
  const canGoNext = resultIndex < results.length - 1

  // Surface partial failures without blocking the rest of the batch.
  const errorCount = results.filter((r) => r.type === 'error').length

  return (
    <div className="flex w-full min-w-0 flex-col gap-4">
      {/* Compact toolbar: navigation + actions in a single tight row. */}
      <div className="flex items-center justify-between gap-3 rounded-lg border border-mcam-navy/15 bg-white px-4 py-2 shadow-sm">
        {/* Left: image navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setResultIndex((i) => Math.max(0, i - 1))}
            disabled={!canGoPrev}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-mcam-navy/20 bg-mcam-surface text-mcam-navy transition-all hover:border-mcam-blue hover:text-mcam-blue disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:text-mcam-muted"
            aria-label="Previous image"
          >
            <ChevronLeft size={14} />
          </button>
          <span className="text-sm tabular-nums text-mcam-navy">
            <span className="font-semibold">{results.length === 0 ? '—' : `${resultIndex + 1}`}</span>
            <span className="text-mcam-muted"> / {results.length}</span>
          </span>
          <button
            onClick={() =>
              setResultIndex((i) => Math.min(results.length - 1, i + 1))
            }
            disabled={!canGoNext}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-mcam-navy/20 bg-mcam-surface text-mcam-navy transition-all hover:border-mcam-blue hover:text-mcam-blue disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:text-mcam-muted"
            aria-label="Next image"
          >
            <ChevronRight size={14} />
          </button>
        </div>

        {errorCount > 0 ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-medium text-red-800 ring-1 ring-red-200">
            {errorCount} failed
          </span>
        ) : null}

        {/* Right: export + upload new */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleExportAll}
            className={reviewActionButtonLg}
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Export all
          </button>
          <button
            type="button"
            onClick={handleExportCsv}
            className={reviewActionButtonLg}
          >
            CSV
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

      {/* Main panel: show either an error card or the success review UI. */}
      {current?.type === 'error' ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-red-200 bg-red-50/80 px-6 py-8 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-100 text-red-600">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
          </div>
          <div>
            <h3 className="text-base font-semibold text-red-900">Could not process image</h3>
            <p className="mt-1 text-sm font-medium text-red-800">{current.file.name}</p>
            <p className="mt-1 text-sm text-red-800">{current.error}</p>
          </div>
          {current.previewUrl && (
            <div className="relative mt-1 h-32 w-32 overflow-hidden rounded-lg border border-red-200 bg-red-50/50">
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
          rerankProgress={current.rerankProgress}
        />
      ) : null}
    </div>
  )
}
