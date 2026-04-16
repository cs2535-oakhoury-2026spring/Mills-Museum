/**
 * Upload and queue UI: pick images, preview the active file, set keyword count,
 * and start batch processing. Supports a per-hierarchy mode where the user can
 * independently choose how many keywords to generate from each AAT hierarchy.
 *
 * Communicates with the parent through
 * `onRequestProcess(files, keywordCount | hierarchyCounts)`.
 */
import { useState, useRef, useEffect } from 'react'

/** Shown in copy as the prediction API host (same default as `App` `VITE_API_URL`). */
const API_HINT =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const DEFAULT_KEYWORD_COUNT = 20
const MIN_KEYWORD_COUNT = 1
const MAX_KEYWORD_COUNT = 50

const PER_HIERARCHY_MIN = 0
const PER_HIERARCHY_MAX = 10
const PER_HIERARCHY_DEFAULT = 2

/**
 * @param {object} props
 * @param {function(File[], number|object): (void|Promise<void>)} props.onRequestProcess
 * @param {string} [props.errorMessage]
 * @param {function(): void} [props.onDismissError]
 */
export default function UploadScreen({
  onRequestProcess,
  errorMessage,
  onDismissError,
}) {
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

  // ── Per-hierarchy state ──
  const [perHierarchyMode, setPerHierarchyMode] = useState(false)
  const [hierarchyNames, setHierarchyNames] = useState([])
  const [hierarchyCounts, setHierarchyCounts] = useState({})
  const [hierarchyTexts, setHierarchyTexts] = useState({})
  const [hierarchyFetchError, setHierarchyFetchError] = useState(false)

  /** Fetch available hierarchies from the backend on mount. */
  useEffect(() => {
    let cancelled = false
    fetch(`${API_HINT}/facets`, {
      headers: { 'ngrok-skip-browser-warning': 'true' },
    })
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return
        const names = data.hierarchies || []
        setHierarchyNames(names)
        const defaults = {}
        const defaultTexts = {}
        for (const n of names) {
          defaults[n] = PER_HIERARCHY_DEFAULT
          defaultTexts[n] = String(PER_HIERARCHY_DEFAULT)
        }
        setHierarchyCounts(defaults)
        setHierarchyTexts(defaultTexts)
      })
      .catch(() => {
        if (!cancelled) setHierarchyFetchError(true)
      })
    return () => { cancelled = true }
  }, [])

  /** Keeps requested term count within API/UI limits (1-50). */
  const clampKeywordCount = (n) => {
    const parsed = Number(n)
    if (!Number.isFinite(parsed)) return DEFAULT_KEYWORD_COUNT
    return Math.max(
      MIN_KEYWORD_COUNT,
      Math.min(MAX_KEYWORD_COUNT, Math.round(parsed)),
    )
  }

  const clampHierarchyCount = (n) => {
    const parsed = Number(n)
    if (!Number.isFinite(parsed)) return PER_HIERARCHY_DEFAULT
    return Math.max(
      PER_HIERARCHY_MIN,
      Math.min(PER_HIERARCHY_MAX, Math.round(parsed)),
    )
  }

  const totalHierarchyCount = Object.values(hierarchyCounts).reduce(
    (sum, v) => sum + v,
    0,
  )

  const updateHierarchyCount = (name, raw) => {
    const next = clampHierarchyCount(raw)
    setHierarchyCounts((prev) => ({ ...prev, [name]: next }))
    setHierarchyTexts((prev) => ({ ...prev, [name]: String(next) }))
  }

  // Object URL for the currently previewed file; revoked on dependency change/unmount.
  useEffect(() => {
    if (files.length === 0) {
      setPreviewUrl(null)
      return undefined
    }
    const url = URL.createObjectURL(files[previewIndex])
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [files, previewIndex])

  // After queue shrinks, keep preview index in range.
  useEffect(() => {
    setPreviewIndex((pi) => {
      if (files.length === 0) return 0
      return Math.min(pi, files.length - 1)
    })
  }, [files])

  /** Replaces the queue from a file input or drop target. */
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

  const canGenerate =
    files.length > 0 &&
    !busy &&
    (perHierarchyMode ? totalHierarchyCount > 0 : true)

  /** Delegates to parent; `busy` prevents re-entry until the handoff completes. */
  const handleProcess = async () => {
    if (!canGenerate) return
    setBusy(true)
    try {
      if (perHierarchyMode) {
        await onRequestProcess(files, hierarchyCounts)
      } else {
        await onRequestProcess(files, keywordCount)
      }
    } finally {
      setBusy(false)
    }
  }

  const showNav = files.length > 1

  const infoCardClass =
    'rounded-xl border-2 border-mcam-navy/20 bg-white p-5 shadow-sm'

  return (
    <div className="grid w-full min-w-0 grid-cols-1 gap-6 lg:grid-cols-12 lg:gap-8">
      {/* Full-width alert from parent when the whole batch failed */}
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

      {/* Left column (lg): large preview + optional multi-file pager */}
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

            {/* Prev/next when more than one file is queued */}
            {showNav ? (
              <div className="flex items-center justify-center gap-3 border-t border-mcam-navy/10 py-2.5">
                <button
                  type="button"
                  onClick={() => setPreviewIndex((i) => Math.max(0, i - 1))}
                  disabled={previewIndex <= 0}
                  className="rounded-md border border-mcam-navy/20 bg-mcam-surface px-2.5 py-1 text-xs text-mcam-navy disabled:cursor-not-allowed disabled:border-mcam-navy/10 disabled:bg-white disabled:text-mcam-muted"
                  aria-label="Previous file preview"
                >
                  &larr;
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
                  &rarr;
                </button>
              </div>
            ) : null}
          </div>

          {/* Scrollable list: select preview row, remove from queue */}
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
                          &times;
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

      {/* Right column (lg): instructions, term count, dropzone, primary CTA */}
      <div className="flex min-w-0 flex-col gap-4 lg:col-span-5">
        {/* Combined How-it-works + Tips card */}
        <div className={infoCardClass}>
          <h3 className="text-sm font-semibold text-mcam-navy">
            How it works
          </h3>
          <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs text-mcam-muted">
            <li>Add one or more artwork images (JPEG, PNG, WebP, and other common formats).</li>
            <li>Run generation; the model proposes AAT-style keywords with confidence scores.</li>
            <li>Review each image, toggle keywords, then copy or export for cataloging.</li>
          </ol>

          <hr className="my-3 border-mcam-navy/10" />

          <h3 className="text-sm font-semibold text-mcam-navy">Tips</h3>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-mcam-muted">
            <li>Treat suggestions as a starting point -- curate before using in records.</li>
            <li>Large batches are processed one image at a time; progress appears after you start.</li>
            <li>If every image fails, check that the API URL is reachable and the server is up.</li>
          </ul>

          <p className="mt-3 text-[11px] leading-relaxed text-mcam-muted">
            Prediction calls go to{' '}
            <code className="rounded border border-mcam-navy/20 bg-mcam-surface px-1 py-0.5 text-mcam-navy">
              {API_HINT}
            </code>
            . Ensure your Google Colab Notebook is running before you start.
          </p>
        </div>

        {/* Keyword count controls */}
        <div className="flex w-full min-w-0 flex-col gap-4">
          {/* Simple mode: single slider */}
          {!perHierarchyMode ? (
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
              <p className="text-[11px] text-mcam-muted">Limits: 1-50 keywords</p>
            </div>
          ) : null}

          {/* Per-hierarchy toggle */}
          {hierarchyNames.length > 0 && !hierarchyFetchError ? (
            <button
              type="button"
              onClick={() => setPerHierarchyMode((v) => !v)}
              className="flex items-center gap-2.5 self-start"
            >
              <span
                className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${
                  perHierarchyMode ? 'bg-mcam-blue' : 'bg-mcam-navy/20'
                }`}
              >
                <span
                  className={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-transform ${
                    perHierarchyMode ? 'translate-x-[18px]' : 'translate-x-[3px]'
                  }`}
                />
              </span>
              <span className="text-xs font-medium text-mcam-navy">
                Per-hierarchy controls
              </span>
            </button>
          ) : null}

          {/* Per-hierarchy sliders */}
          {perHierarchyMode && hierarchyNames.length > 0 ? (
            <div className={`${infoCardClass} flex flex-col gap-3`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-mcam-navy">
                  Keywords per hierarchy
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                    totalHierarchyCount === 0
                      ? 'bg-red-100 text-red-700'
                      : 'bg-mcam-blue-light text-mcam-navy'
                  }`}
                >
                  Total: {totalHierarchyCount}
                </span>
              </div>

              {totalHierarchyCount === 0 ? (
                <p className="text-[11px] text-red-600">
                  Set at least one hierarchy above 0 to generate keywords.
                </p>
              ) : null}

              <div className="max-h-72 space-y-2.5 overflow-y-auto overscroll-contain pr-1">
                {hierarchyNames.map((name) => (
                  <div key={name} className="flex items-center gap-2">
                    <span className="w-[140px] shrink-0 truncate text-[11px] font-medium text-mcam-navy" title={name}>
                      {name}
                    </span>
                    <input
                      type="range"
                      min={PER_HIERARCHY_MIN}
                      max={PER_HIERARCHY_MAX}
                      step={1}
                      value={hierarchyCounts[name] ?? PER_HIERARCHY_DEFAULT}
                      onChange={(e) => updateHierarchyCount(name, e.target.value)}
                      className="h-1.5 w-full min-w-0 cursor-pointer accent-mcam-navy"
                      aria-label={`${name} keyword count`}
                    />
                    <input
                      type="number"
                      min={PER_HIERARCHY_MIN}
                      max={PER_HIERARCHY_MAX}
                      step={1}
                      value={hierarchyTexts[name] ?? String(PER_HIERARCHY_DEFAULT)}
                      onChange={(e) => {
                        const nextText = e.target.value
                        setHierarchyTexts((prev) => ({ ...prev, [name]: nextText }))
                        if (nextText === '') return
                        const parsed = parseInt(nextText, 10)
                        if (Number.isNaN(parsed)) return
                        const clamped = clampHierarchyCount(parsed)
                        setHierarchyCounts((prev) => ({ ...prev, [name]: clamped }))
                        if (String(clamped) !== nextText) {
                          setHierarchyTexts((prev) => ({ ...prev, [name]: String(clamped) }))
                        }
                      }}
                      onBlur={() => {
                        if ((hierarchyTexts[name] ?? '') === '') {
                          const current = hierarchyCounts[name] ?? PER_HIERARCHY_DEFAULT
                          setHierarchyTexts((prev) => ({ ...prev, [name]: String(current) }))
                        }
                      }}
                      className="w-14 shrink-0 rounded-md border-2 border-mcam-navy/25 bg-white py-1 px-1.5 text-center text-xs text-mcam-navy focus:border-mcam-blue focus:outline-none"
                      aria-label={`${name} keyword count (number)`}
                    />
                  </div>
                ))}
              </div>

              <p className="text-[11px] text-mcam-muted">
                0-10 per hierarchy. Set 0 to exclude a hierarchy.
              </p>
            </div>
          ) : null}

          {/* Accessible drop target; hidden `<input type="file">` opened programmatically */}
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
                or click &middot; multiple OK
              </p>
            </div>
            <span className="rounded-md border border-mcam-navy/15 bg-mcam-surface px-2.5 py-1 text-[11px] font-medium text-mcam-navy transition-all group-hover:border-mcam-blue/50 group-hover:bg-mcam-blue-light group-hover:text-mcam-blue">
              Choose files
            </span>
          </div>

          {/* Hands off to `App.handleRequestProcess`; disabled while `busy` or queue empty */}
          <button
            type="button"
            onClick={handleProcess}
            disabled={!canGenerate}
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
