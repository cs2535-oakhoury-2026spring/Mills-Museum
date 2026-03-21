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
    <div className="mx-auto flex w-full max-w-md flex-col items-center gap-5">
      {errorMessage ? (
        <div
          className="w-full rounded-lg border border-amber-700/50 bg-amber-950/40 px-3 py-2.5 text-sm text-amber-100"
          role="alert"
        >
          <div className="flex flex-wrap items-start justify-between gap-2">
            <span>{errorMessage}</span>
            <button
              type="button"
              onClick={onDismissError}
              className="shrink-0 text-amber-300 underline hover:text-amber-200"
            >
              Dismiss
            </button>
          </div>
        </div>
      ) : null}

      <div className="w-full overflow-hidden rounded-xl bg-slate-800 ring-1 ring-slate-700">
        <div className="flex h-44 items-center justify-center bg-slate-900/70 px-2">
          {previewUrl ? (
            <img
              src={previewUrl}
              alt={`Preview ${previewIndex + 1} of ${files.length}`}
              className="max-h-full max-w-full object-contain"
            />
          ) : (
            <span className="text-xs text-slate-500">No image selected</span>
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

      <div
        className={`w-full rounded-xl bg-slate-800 px-4 py-4 ring-1 transition-all ${
          isDragging ? 'ring-2 ring-amber-500' : 'ring-slate-700'
        }`}
        role="button"
        tabIndex={0}
        aria-label="Upload artwork images"
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
          multiple
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div
          className={`flex flex-col items-center justify-center rounded-lg border border-dashed py-5 transition-colors ${
            isDragging ? 'border-amber-500/80 bg-amber-950/20' : 'border-slate-600 bg-slate-700/30'
          }`}
        >
          <p className="text-center text-sm text-slate-300">Drop images here</p>
          <p className="mt-1 text-center text-xs text-slate-500">or click to choose · multiple files OK</p>
          <span className="mt-3 inline-flex rounded-md bg-amber-500 px-5 py-2 text-xs font-medium text-slate-900">
            Choose files
          </span>
        </div>
      </div>

      <button
        type="button"
        onClick={handleProcess}
        disabled={files.length === 0 || busy}
        className="w-full max-w-xs rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? 'Working…' : 'Generate keywords'}
      </button>
    </div>
  )
}
