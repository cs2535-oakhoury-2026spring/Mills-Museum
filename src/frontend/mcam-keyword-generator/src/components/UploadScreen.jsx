import { useState, useRef, useEffect } from 'react'

export default function UploadScreen({
  onRequestProcess,
  errorMessage,
  onDismissError,
}) {
  const DEFAULT_KEYWORD_COUNT = 20
  const MIN_KEYWORD_COUNT = 1
  const MAX_KEYWORD_COUNT = 50

  const [files, setFiles] = useState([])
  const [previewIndex, setPreviewIndex] = useState(0)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [busy, setBusy] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [keywordCount, setKeywordCount] = useState(DEFAULT_KEYWORD_COUNT)
  const [keywordCountText, setKeywordCountText] = useState(
    String(DEFAULT_KEYWORD_COUNT),
  )
  const inputRef = useRef(null)

  const clampKeywordCount = (n) => {
    const parsed = Number(n)
    if (!Number.isFinite(parsed)) return DEFAULT_KEYWORD_COUNT
    return Math.max(
      MIN_KEYWORD_COUNT,
      Math.min(MAX_KEYWORD_COUNT, Math.round(parsed)),
    )
  }

  useEffect(() => {
    if (files.length === 0) {
      setPreviewUrl(null)
      return undefined
    }
    const url = URL.createObjectURL(files[previewIndex])
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [files, previewIndex])

  const handleFiles = (incoming) => {
    const arr = Array.from(incoming || [])
    setFiles(arr)
    setPreviewIndex(0)
    onDismissError?.()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  const handleProcess = async () => {
    if (files.length === 0 || busy) return
    setBusy(true)
    try {
      await onRequestProcess(files, keywordCount)
    } finally {
      setBusy(false)
    }
  }

  const showNav = files.length > 1

  return (
    <div className="flex w-full min-w-0 flex-col gap-6 overflow-x-hidden">
      {errorMessage ? (
        <div className="flex min-w-0 items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300 shadow-lg shadow-red-500/5">
          <svg className="h-5 w-5 shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          <span className="min-w-0 flex-1 font-medium">{errorMessage}</span>
          <button
            type="button"
            onClick={onDismissError}
            className="shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium text-red-300 transition-colors hover:bg-red-500/20"
          >
            Dismiss
          </button>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-col gap-5">
        {/* Fixed-size preview; image is positioned so intrinsic width cannot expand layout */}
        <div className="w-full min-w-0 overflow-hidden rounded-xl bg-slate-800 ring-1 ring-slate-700">
          <div className="relative h-80 min-h-80 w-full min-w-0 bg-slate-900/70">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt={`Preview ${previewIndex + 1} of ${files.length}`}
                className="absolute inset-0 box-border h-full w-full object-contain object-center"
              />
            ) : (
              <span className="absolute inset-0 flex items-center justify-center text-xs text-slate-500">
                No image selected
              </span>
            )}
          </div>

          {showNav ? (
            <div className="flex items-center justify-center gap-3 border-t border-slate-700 py-2.5">
              <button
                type="button"
                onClick={() => setPreviewIndex((i) => Math.max(0, i - 1))}
                disabled={previewIndex <= 0}
                className="rounded-md bg-slate-700 px-2.5 py-1 text-xs text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Previous file preview"
              >
                ←
              </button>
              <span className="min-w-[5rem] text-center text-xs text-slate-400">
                {previewIndex + 1} / {files.length}
              </span>
              <button
                type="button"
                onClick={() =>
                  setPreviewIndex((i) => Math.min(files.length - 1, i + 1))
                }
                disabled={previewIndex >= files.length - 1}
                className="rounded-md bg-slate-700 px-2.5 py-1 text-xs text-slate-200 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Next file preview"
              >
                →
              </button>
            </div>
          ) : null}
        </div>

        <div className="flex w-full min-w-0 flex-col gap-3">
        <div className="flex min-w-0 flex-col gap-2">
          <label className="text-xs font-medium text-slate-200" htmlFor="kw-count">
            # Keywords to generate
          </label>
          <div className="flex items-center gap-3">
            <input
              id="kw-count"
              type="range"
              min={MIN_KEYWORD_COUNT}
              max={MAX_KEYWORD_COUNT}
              step={1}
              value={keywordCount}
              onChange={(e) => {
                const next = clampKeywordCount(e.target.value)
                setKeywordCount(next)
                setKeywordCountText(String(next))
              }}
              className="h-2 w-full cursor-pointer accent-amber-500"
              aria-label="Keyword count"
            />
            <input
              type="number"
              min={MIN_KEYWORD_COUNT}
              max={MAX_KEYWORD_COUNT}
              step={1}
              value={keywordCountText}
              onChange={(e) => {
                const nextText = e.target.value
                setKeywordCountText(nextText)

                // Allow the field to be temporarily empty while editing.
                if (nextText === '') return

                const parsed = parseInt(nextText, 10)
                if (Number.isNaN(parsed)) return

                const next = clampKeywordCount(parsed)
                setKeywordCount(next)
                // Normalize out-of-range values immediately.
                if (String(next) !== nextText) {
                  setKeywordCountText(String(next))
                }
              }}
              onBlur={() => {
                if (keywordCountText === '') {
                  setKeywordCountText(String(keywordCount))
                }
              }}
              className="w-20 rounded-md bg-slate-900/80 py-2 px-2 text-sm text-slate-100 ring-1 ring-slate-600 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/70"
              aria-label="Keyword count (number)"
            />
          </div>
          <p className="text-[11px] text-slate-500">Limits: 1–50 keywords</p>
        </div>

          <div
            tabIndex={0}
            role="button"
            className={`group flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-lg border-2 border-dashed px-3 py-3 transition-all duration-200 ${
              isDragging
                ? 'border-amber-500 bg-amber-500/10 shadow-lg shadow-amber-500/10'
                : 'border-slate-700 bg-slate-900/30 hover:border-amber-500/50 hover:bg-slate-900/50'
            }`}
            onClick={() => inputRef.current?.click?.()}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                inputRef.current?.click?.()
              }
            }}
            onDrop={handleDrop}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={(e) => {
              e.preventDefault()
              setIsDragging(false)
            }}
            onDragEnter={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-800 text-slate-400 ring-1 ring-slate-700 transition-all group-hover:bg-amber-500/10 group-hover:text-amber-400 group-hover:ring-amber-500/30">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-xs font-semibold text-slate-200">
                Drop images here
              </p>
              <p className="mt-0.5 text-[11px] text-slate-500">
                or click · multiple OK
              </p>
            </div>
            <span className="rounded-md bg-slate-800 px-2.5 py-1 text-[11px] font-medium text-slate-300 ring-1 ring-slate-700 transition-all group-hover:bg-amber-500/20 group-hover:text-amber-300 group-hover:ring-amber-500/30">
              Choose files
            </span>
          </div>

          <button
            type="button"
            onClick={handleProcess}
            disabled={files.length === 0 || busy}
            className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-amber-500/25 transition-all hover:from-amber-400 hover:to-orange-400 hover:shadow-amber-500/40 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
          >
            {busy ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processing...
              </span>
            ) : (
              'Generate Keywords'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
