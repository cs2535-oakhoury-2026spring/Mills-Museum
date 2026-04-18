import { ResultDisplay } from './ResultDisplay'
import {
  buildCombinedExportCsv,
  buildCombinedExportText,
  downloadTextFile,
} from '../utils/keywordAdapters'

/**
 * Batch review "shell" for results.
 *
 * Navigation, batch export, and "upload new" controls are passed down to
 * ResultDisplay so they render underneath the image preview (left column).
 */
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

  const handleExportCsv = () => {
    const csv = buildCombinedExportCsv(results)
    downloadTextFile('mcam_keywords_export.csv', csv)
  }

  const canGoPrev = resultIndex > 0
  const canGoNext = resultIndex < results.length - 1
  const errorCount = results.filter((r) => r.type === 'error').length

  const navProps = {
    resultIndex,
    resultCount: results.length,
    canGoPrev,
    canGoNext,
    onPrev: () => setResultIndex((i) => Math.max(0, i - 1)),
    onNext: () => setResultIndex((i) => Math.min(results.length - 1, i + 1)),
    errorCount,
    onExportAll: handleExportAll,
    onExportCsv: handleExportCsv,
    onUploadNew,
  }

  return (
    <div className="flex w-full min-w-0 flex-col gap-4">
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
          description={current.description}
          retrievalStats={current.retrievalStats}
          rerankProgress={current.rerankProgress}
          nav={navProps}
        />
      ) : null}
    </div>
  )
}
