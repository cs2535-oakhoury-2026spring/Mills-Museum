import { useState, useRef, useEffect } from 'react'

const API_HINT =
  import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

  useEffect(() => {
    setPreviewIndex((pi) => {
      if (files.length === 0) return 0
      return Math.min(pi, files.length - 1)
    })
  }, [files])

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

  const removeFileAt = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx))
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

  const infoCardClass =
    'rounded-xl border-2 border-mcam-navy/20 bg-white p-4 shadow-sm'

  return (
    <div className="grid w-full min-w-0 grid-cols-1 gap-6 lg:grid-cols-12 lg:gap-8">
      {errorMessage ? (
        <div className="flex min-w-0 items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 shadow-sm lg:col-span-12">
          <svg className="h-5 w-5 shrink-0 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          <span className="min-w-0 flex-1 font-medium">{errorMessage}</span>
          <button
            type="button"
            onClick={onDismissError}
            className="shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-100"
          >
            Dismiss
          </button>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-col gap-4 lg:col-span-7">
        <div className="flex min-w-0 flex-col gap-4">
          <div className="min-w-0 rounded-xl border-2 border-mcam-navy/25 bg-white shadow-sm">
            <div className="relative h-72 min-h-72 w-full min-w-0 overflow-hidden bg-mcam-surface sm:h-80 sm:min-h-80 lg:h-96 lg:min-h-96">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt={`Preview ${previewIndex + 1} of ${files.length}`}
                  className="absolute inset-0 box-border h-full w-full max-h-full max-w-full object-contain object-center p-2"
                />
              ) : (
                <span className="absolute inset-0 flex items-center justify-center text-xs text-mcam-muted">
                  No image selected
                </span>
              )}
            </div>

            {showNav ? (
              <div className="flex items-center justify-center gap-3 border-t border-mcam-navy/10 py-2.5">
                <button
                  type="button"
                  onClick={() => setPreviewIndex((i) => Math.max(0, i - 1))}
                  disabled={previewIndex <= 0}
                  className="rounded-md border border-mcam-navy/20 bg-mcam-surface px-2.5 py-1 text-xs text-mcam-navy disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:bg-white disabled:text-mcam-muted"
                  aria-label="Previous file preview"
                >
                  ←
                </button>
                <span className="min-w-[5rem] text-center text-xs text-mcam-muted">
                  {previewIndex + 1} / {files.length}
                </span>
                <button
                  type="button"
                  onClick={() =>
                    setPreviewIndex((i) => Math.min(files.length - 1, i + 1))
                  }
                  disabled={previewIndex >= files.length - 1}
                  className="rounded-md border border-mcam-navy/20 bg-mcam-surface px-2.5 py-1 text-xs text-mcam-navy disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:bg-white disabled:text-mcam-muted"
                  aria-label="Next file preview"
                >
                  →
                </button>
              </div>
            ) : null}
          </div>

          {files.length > 0 ? (
            <div className={`${infoCardClass} flex min-h-0 w-full flex-col`}>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-mcam-muted">
                Queue ({files.length})
              </p>
              <ul className="max-h-52 space-y-1 overflow-y-auto overscroll-contain sm:max-h-64">
                {files.map((file, i) => {
                  const selected = i === previewIndex
                  return (
                    <li key={`${file.name}-${i}`} className="min-w-0">
                      <div
                        className={`flex items-center gap-1 rounded-lg py-1 pl-2 pr-1 transition-colors ${
                          selected
                            ? 'border border-mcam-blue/50 bg-mcam-blue-light'
                            : 'border border-transparent bg-mcam-surface hover:border-mcam-navy/15'
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => setPreviewIndex(i)}
                          className="min-w-0 flex-1 truncate text-left text-xs font-medium text-mcam-navy"
                          title={file.name}
                        >
                          {file.name}
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            removeFileAt(i)
                          }}
                          className="shrink-0 rounded-md px-1.5 py-1 text-xs text-mcam-muted transition-colors hover:bg-red-50 hover:text-red-700"
                          aria-label={`Remove ${file.name}`}
                        >
                          ×
                        </button>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          ) : null}
        </div>
      </div>

      <div className="flex min-w-0 flex-col gap-5 lg:col-span-5">
        <div className={infoCardClass}>
          <h3 className="text-sm font-semibold text-mcam-navy">
            How it works
          </h3>
          <ol className="mt-2 list-decimal space-y-1.5 pl-4 text-xs text-mcam-muted">
            <li>Add one or more artwork images (JPEG, PNG, WebP, and other common formats).</li>
            <li>Run generation; the model proposes AAT-style keywords with confidence scores.</li>
            <li>Review each image, toggle keywords, then copy or export for cataloging.</li>
          </ol>
          <p className="mt-3 text-[11px] leading-relaxed text-mcam-muted">
            Prediction calls go to{' '}
            <code className="rounded border border-mcam-navy/20 bg-mcam-surface px-1 py-0.5 text-mcam-navy">
              {API_HINT}
            </code>
            . Ensure your Google Colab Notebook is running before you start.
          </p>
        </div>

        <div className={infoCardClass}>
          <h3 className="text-sm font-semibold text-mcam-navy">Tips</h3>
          <ul className="mt-2 list-disc space-y-1.5 pl-4 text-xs text-mcam-muted">
            <li>Treat suggestions as a starting point—curate before using in records.</li>
            <li>Large batches are processed one image at a time; progress appears after you start.</li>
            <li>If every image fails, check that the API URL is reachable and the server is up.</li>
          </ul>
        </div>

        <div className="flex w-full min-w-0 flex-col gap-3">
          <div className="flex min-w-0 flex-col gap-2">
            <label className="text-xs font-medium text-mcam-navy" htmlFor="kw-count">
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
                className="h-2 w-full cursor-pointer accent-mcam-navy"
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

                  if (nextText === '') return

                  const parsed = parseInt(nextText, 10)
                  if (Number.isNaN(parsed)) return

                  const next = clampKeywordCount(parsed)
                  setKeywordCount(next)
                  if (String(next) !== nextText) {
                    setKeywordCountText(String(next))
                  }
                }}
                onBlur={() => {
                  if (keywordCountText === '') {
                    setKeywordCountText(String(keywordCount))
                  }
                }}
                className="w-20 rounded-md border-2 border-mcam-navy/25 bg-white py-2 px-2 text-sm text-mcam-navy placeholder:text-mcam-muted focus:border-mcam-blue focus:outline-none"
                aria-label="Keyword count (number)"
              />
            </div>
            <p className="text-[11px] text-mcam-muted">Limits: 1–50 keywords</p>
          </div>

          <div
            tabIndex={0}
            role="button"
            className={`group flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-lg border-2 border-dashed px-3 py-3 transition-all duration-200 ${
              isDragging
                ? 'border-mcam-blue bg-mcam-blue-light shadow-md'
                : 'border-mcam-navy/30 bg-white hover:border-mcam-blue hover:bg-mcam-blue-light/80'
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
            <div className="flex h-8 w-8 items-center justify-center rounded-md border border-mcam-navy/15 bg-mcam-surface text-mcam-muted transition-all group-hover:border-mcam-blue/40 group-hover:bg-mcam-blue-light group-hover:text-mcam-blue">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-xs font-semibold text-mcam-navy">
                Drop images here
              </p>
              <p className="mt-0.5 text-[11px] text-mcam-muted">
                or click · multiple OK
              </p>
            </div>
            <span className="rounded-md border border-mcam-navy/15 bg-mcam-surface px-2.5 py-1 text-[11px] font-medium text-mcam-navy transition-all group-hover:border-mcam-blue/50 group-hover:bg-mcam-blue-light group-hover:text-mcam-blue">
              Choose files
            </span>
          </div>

          <button
            type="button"
            onClick={handleProcess}
            disabled={files.length === 0 || busy}
            className="w-full rounded-xl border-2 border-[#1e2a44]/35 bg-[#1e2a44] px-4 py-3 text-sm font-semibold !text-white shadow-md transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:border-[#c5cedd] disabled:bg-[#e8ecf2] disabled:!text-[#3d4d66] disabled:shadow-none"
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
