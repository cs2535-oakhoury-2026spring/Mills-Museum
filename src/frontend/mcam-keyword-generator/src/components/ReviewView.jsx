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

  return (
    <div className="w-full">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setResultIndex((i) => Math.max(0, i - 1))}
            disabled={!canGoPrev}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-slate-200 ring-1 ring-slate-700 transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Previous image"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="min-w-[6rem] text-center text-sm font-medium text-slate-300">
            {results.length === 0 ? '—' : `${resultIndex + 1} / ${results.length}`}
          </span>
          <button
            type="button"
            onClick={() =>
              setResultIndex((i) => Math.min(results.length - 1, i + 1))
            }
            disabled={!canGoNext}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-800 text-slate-200 ring-1 ring-slate-700 transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Next image"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>

        <div className="flex flex-wrap gap-2 sm:justify-end">
          <button
            type="button"
            onClick={handleExportAll}
            className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 ring-1 ring-slate-600 transition-colors hover:bg-slate-600"
          >
            Export all (text)
          </button>
          <button
            type="button"
            onClick={onUploadNew}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-slate-900 transition-colors hover:bg-amber-400"
          >
            Upload new
          </button>
        </div>
      </div>

      {current?.type === 'error' ? (
        <div className="rounded-xl border border-red-900/40 bg-slate-800 p-5 ring-1 ring-slate-700">
          <h2 className="text-sm font-medium text-red-400">Could not process image</h2>
          <p className="mt-1.5 text-sm text-slate-300">{current.file.name}</p>
          <p className="mt-1 text-sm text-slate-500">{current.error}</p>
          <div className="mt-4 max-h-64 overflow-hidden rounded-lg bg-slate-900">
            <img
              src={current.previewUrl}
              alt=""
              className="mx-auto max-h-64 w-full object-contain"
            />
          </div>
        </div>
      ) : current?.type === 'success' ? (
        <ResultDisplay
          imageSrc={current.previewUrl}
          keywords={current.keywords}
          onKeywordsChange={(next) => onKeywordsChange(resultIndex, next)}
          fileName={current.file.name}
        />
      ) : null}
    </div>
  )
}
