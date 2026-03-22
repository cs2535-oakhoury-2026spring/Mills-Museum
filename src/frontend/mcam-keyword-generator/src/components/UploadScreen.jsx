import { useState, useRef, useEffect } from 'react'

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
  const inputRef = useRef(null)

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
      await onRequestProcess(files)
    } finally {
      setBusy(false)
    }
  }

  const showNav = files.length > 1

  return (
    <div className="flex flex-col gap-6">
      {/* Error Banner */}
      {errorMessage ? (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 px-5 py-4 text-sm text-red-300 shadow-lg shadow-red-500/5">
          <svg className="h-5 w-5 shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
          <span className="flex-1 font-medium">{errorMessage}</span>
          <button
            onClick={onDismissError}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-red-300 transition-colors hover:bg-red-500/20"
          >
            Dismiss
          </button>
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Preview Panel */}
        <div className="flex flex-col gap-3">
          <div className="relative flex aspect-square items-center justify-center overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/50 shadow-inner">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Preview"
                className="h-full w-full object-contain p-4 transition-opacity duration-300"
              />
            ) : (
              <div className="flex flex-col items-center gap-2 text-slate-600">
                <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
                </svg>
                <span className="text-sm">No image selected</span>
              </div>
            )}
          </div>

          {showNav ? (
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={() => setPreviewIndex((i) => Math.max(0, i - 1))}
                disabled={previewIndex <= 0}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-slate-300 ring-1 ring-slate-700 transition-all hover:bg-slate-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Previous file preview"
              >
                ←
              </button>
              <span className="min-w-[4rem] text-center text-sm font-medium text-slate-400">
                {previewIndex + 1} / {files.length}
              </span>
              <button
                onClick={() =>
                  setPreviewIndex((i) => Math.min(files.length - 1, i + 1))
                }
                disabled={previewIndex >= files.length - 1}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-slate-300 ring-1 ring-slate-700 transition-all hover:bg-slate-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Next file preview"
              >
                →
              </button>
            </div>
          ) : null}
        </div>

        {/* Upload Panel */}
        <div className="flex flex-col gap-4">
          <div
            tabIndex={0}
            role="button"
            className={`group flex flex-1 cursor-pointer flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed p-8 transition-all duration-200 ${
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
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800 text-slate-400 ring-1 ring-slate-700 transition-all group-hover:bg-amber-500/10 group-hover:text-amber-400 group-hover:ring-amber-500/30">
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-base font-semibold text-slate-200">
                Drop images here
              </p>
              <p className="mt-1 text-sm text-slate-500">
                or click to choose · multiple files supported
              </p>
            </div>
            <span className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 ring-1 ring-slate-700 transition-all group-hover:bg-amber-500/20 group-hover:text-amber-300 group-hover:ring-amber-500/30">
              Choose files
            </span>
          </div>

          {files.length > 0 && (
            <div className="rounded-xl border border-slate-800/60 bg-slate-900/30 px-4 py-3">
              <p className="text-sm text-slate-400">
                <span className="font-semibold text-white">{files.length}</span>{' '}
                {files.length === 1 ? 'image' : 'images'} selected
              </p>
            </div>
          )}

          <button
            onClick={handleProcess}
            disabled={files.length === 0 || busy}
            className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-amber-500/25 transition-all hover:from-amber-400 hover:to-orange-400 hover:shadow-amber-500/40 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
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
