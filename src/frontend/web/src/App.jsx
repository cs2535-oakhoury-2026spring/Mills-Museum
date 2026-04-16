/**
 * Root application shell for the MCAM Keyword Generator.
 *
 * Drives a three-phase flow: `upload` → `processing` → `result` (review).
 * Each selected image is POSTed to `/predict` with `term_count`; responses are
 * normalized via `mapApiKeyword`. Object URLs for previews are revoked when
 * resetting or when the whole batch fails to avoid leaks.
 */
import { useState, useCallback } from 'react'
import logoUrl from '../../../../media/logo.png'
import UploadScreen from './components/UploadScreen'
import ReviewView from './components/ReviewView'
import { ProcessingDisplay } from './components/ProcessingDisplay'
import { mapApiKeyword } from './utils/keywordAdapters'

/** Backend base URL (override with `VITE_API_URL`). */
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [phase, setPhase] = useState('upload')
  const [results, setResults] = useState([])
  const [resultIndex, setResultIndex] = useState(0)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingPreviewUrl, setProcessingPreviewUrl] = useState('')
  const [processingLabel, setProcessingLabel] = useState('')
  const [batchError, setBatchError] = useState('')

  /** Revokes blob URLs created for result thumbnails (call before discarding rows). */
  const revokeResultUrls = useCallback((list) => {
    list.forEach((r) => {
      if (r.previewUrl) URL.revokeObjectURL(r.previewUrl)
    })
  }, [])

  /**
   * Sequentially uploads each file to `/predict`, updates the processing UI,
   * and collects success or error rows. If every request fails, revokes URLs
   * and returns to upload with `batchError`; otherwise switches to `result`.
   *
   * @param {File[]} files
   * @param {number} [termCount=20] Clamped to 1–50 server-side style in this handler.
   */
  const handleRequestProcess = async (files, termCount = 20) => {
    if (!files.length) return
    setBatchError('')
    setPhase('processing')
    setProcessingProgress(0)
    setProcessingPreviewUrl('')
    const acc = []
    const clampedTermCount = (() => {
      const n = Number(termCount)
      if (!Number.isFinite(n)) return 20
      return Math.max(1, Math.min(50, Math.round(n)))
    })()

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const previewUrl = URL.createObjectURL(file)
      setProcessingPreviewUrl(previewUrl)
      setProcessingLabel(`Processing image ${i + 1} of ${files.length}`)
      const t0 = performance.now()
      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('term_count', String(clampedTermCount))
        const res = await fetch(`${API_URL}/predict`, {
          method: 'POST',
          headers: { 'ngrok-skip-browser-warning': 'true' },
          body: formData,
        })
        if (!res.ok) throw new Error(`Server error: ${res.status}`)
        const data = await res.json()
        const t1 = performance.now()
        acc.push({
          type: 'success',
          file,
          previewUrl,
          keywords: (data.keywords || [])
            .map(mapApiKeyword)
            .filter((k) => k.text),
          processingTime: (t1 - t0) / 1000,
        })
      } catch (err) {
        console.error(err)
        acc.push({
          type: 'error',
          file,
          previewUrl,
          error:
            err?.message ||
            'Error connecting to backend. Is the Colab running?',
        })
      }
      setProcessingProgress(((i + 1) / files.length) * 100)
    }

    const ok = acc.filter((r) => r.type === 'success')
    if (ok.length === 0) {
      revokeResultUrls(acc)
      setPhase('upload')
      setBatchError('Every image failed. Check the backend and try again.')
      return
    }

    setResults(acc)
    setResultIndex(0)
    setPhase('result')
  }

  /** Clears results, revokes preview URLs, and returns to the upload phase. */
  const handleUploadNew = () => {
    revokeResultUrls(results)
    setResults([])
    setResultIndex(0)
    setPhase('upload')
    setBatchError('')
  }

  /**
   * Persists edited keywords for one successful result row (ReviewView).
   * @param {number} idx
   * @param {Array<{ text: string, confidence: number, [key: string]: unknown }>} nextKeywords UI keyword objects (same shape as `mapApiKeyword` output).
   */
  const handleKeywordsChange = (idx, nextKeywords) => {
    setResults((prev) => {
      const copy = [...prev]
      const row = copy[idx]
      if (row?.type === 'success') {
        copy[idx] = { ...row, keywords: nextKeywords }
      }
      return copy
    })
  }

  return (
    <div className="mcam-app flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-white to-mcam-surface text-mcam-navy">
      {/* Sticky top bar: museum branding + live phase indicator */}
      <header className="sticky top-0 z-30 border-b-2 border-mcam-navy/15 bg-white/95 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <img
              src={logoUrl}
              alt="Mills College Art Museum"
              className="h-9 w-auto max-w-[200px] object-contain object-left"
            />
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-mcam-navy">
                MCAM Keyword Generator
              </h1>
              <p className="text-xs text-mcam-muted">Art & Architecture Thesaurus Pipeline</p>
            </div>
          </div>
          {/* Ready | Processing | Review — mirrors `phase` */}
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[#2f62a8]/50 bg-[#d8e4f5] px-3 py-1 text-xs font-semibold text-[#1e2a44]">
              <span
                className="h-2 w-2 shrink-0 rounded-full bg-[#2f62a8] shadow-sm ring-2 ring-white"
                aria-hidden
              />
              {phase === 'upload'
                ? 'Ready'
                : phase === 'processing'
                  ? 'Processing'
                  : 'Review'}
            </span>
          </div>
        </div>
      </header>

      {/* Primary content: exactly one of upload hero + screen | processing | review */}
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-8 sm:px-6 sm:py-10">
        {/* Hero blurb only on upload; processing/result have their own headings */}
        {phase === 'upload' ? (
          <div className="mb-8 text-center">
            <h2 className="text-xl font-semibold text-mcam-navy sm:text-2xl">
              MCAM Art Keyword Generator
            </h2>
            <p className="mcam-subtitle mx-auto mt-2 max-w-2xl text-mcam-muted">
              Upload artwork images to automatically generate AAT keywords for
              cataloging.
            </p>
          </div>
        ) : null}

        <div className="flex w-full min-w-0 flex-1 justify-center">
          {/* Upload: file queue + generate */}
          {phase === 'upload' ? (
            <div className="mx-auto w-full min-w-0 max-w-6xl shrink-0">
              <UploadScreen
                onRequestProcess={handleRequestProcess}
                errorMessage={batchError}
                onDismissError={() => setBatchError('')}
              />
            </div>
          ) : null}

          {/* Per-file progress + preview while `/predict` runs */}
          {phase === 'processing' ? (
            <ProcessingDisplay
              progress={processingProgress}
              imageSrc={processingPreviewUrl}
              keywords={[]}
              statusLabel={processingLabel}
            />
          ) : null}

          {/* Batch results: navigate images, edit keywords, export */}
          {phase === 'result' ? (
            <div className="w-full min-w-0">
              <ReviewView
                results={results}
                resultIndex={resultIndex}
                setResultIndex={setResultIndex}
                onUploadNew={handleUploadNew}
                onKeywordsChange={handleKeywordsChange}
              />
            </div>
          ) : null}
        </div>
      </main>

      <footer className="border-t-2 border-mcam-navy/15 bg-white/90 py-4 text-center text-xs text-mcam-muted">
        {/* Static footer strip */}
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          AAT keyword pipeline
        </div>
      </footer>
    </div>
  )
}
