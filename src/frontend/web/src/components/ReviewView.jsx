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
    // Build one combined plain-text export for the entire batch.
    // Only keywords the reviewer left "included" are written out.
    const text = buildCombinedExportText(results)
    downloadTextFile('mcam_keywords_export.txt', text)
  }

  const handleExportCsv = () => {
    // Build a spreadsheet-friendly version of the same batch export.
    const csv = buildCombinedExportCsv(results)
    downloadTextFile('mcam_keywords_export.csv', csv)
  }

  // Clamp navigation via derived booleans and guarded index updates.
  const canGoPrev = resultIndex > 0
  const canGoNext = resultIndex < results.length - 1

  // Surface partial failures without blocking the rest of the batch.
  const errorCount = results.filter((r) => r.type === 'error').length

  return (
    <div className="mx-auto flex w-full max-w-6xl min-w-0 flex-col gap-6">
      {/* Review header: navigation, batch status, and global actions. */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border-2 border-mcam-navy/20 bg-white px-6 py-4 shadow-sm">
        {/* Left section: move between results in this batch. */}
        <div className="flex items-center gap-3">
          {/* Previous result button (disabled on first item). */}
          <button
            onClick={() => setResultIndex((i) => Math.max(0, i - 1))}
            disabled={!canGoPrev}
            className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-mcam-navy/20 bg-mcam-surface text-mcam-navy transition-all hover:border-mcam-blue hover:bg-mcam-blue-light hover:text-mcam-blue disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:bg-white disabled:text-mcam-muted"
            aria-label="Previous image"
          >
            <ChevronLeft size={18} />
          </button>
          {/* Position indicator: current result out of total. */}
          <div className="text-center">
            <span className="text-lg font-bold text-mcam-navy">
              {results.length === 0 ? '—' : `${resultIndex + 1}`}
            </span>
            <span className="text-lg text-mcam-muted"> / {results.length}</span>
          </div>
          {/* Next result button (disabled on last item). */}
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
          /* Center section: shows how many files failed processing. */
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-800 ring-1 ring-red-200">
              {errorCount} failed
            </span>
          </div>
        ) : null}

        {/* Right section: export results or start a new upload batch. */}
        <div className="flex items-center gap-2">
          {/* Export combined plain-text output. */}
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
          {/* Export combined CSV output for spreadsheets. */}
          <button
            type="button"
            onClick={handleExportCsv}
            className={reviewActionButtonLg}
          >
            CSV
          </button>
          {/* Return to uploader for a new set of images. */}
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
        // Errors are displayed inline so users can still navigate the batch
        // and export other successful results.
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-red-200 bg-red-50/80 px-8 py-12 text-center">
          {/* Error icon to highlight failed processing state. */}
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100 text-red-600">
            <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
            </svg>
          </div>
          {/* Error details: title, filename, and backend message. */}
          <div>
            <h3 className="text-lg font-semibold text-red-900">Could not process image</h3>
            <p className="mt-1 text-sm font-medium text-red-800">{current.file.name}</p>
            <p className="mt-2 text-sm text-red-800">{current.error}</p>
          </div>
          {current.previewUrl && (
            /* Optional thumbnail for the failed image. */
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
        // Success state delegates keyword review/editing to ResultDisplay.
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
