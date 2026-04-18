/**
 * Root application shell for the MCAM Keyword Generator.
 *
 * Drives a three-phase flow: `upload` → `processing` → `result` (review).
 * Each selected image is POSTed to `/predict-stream` (SSE with VLM description
 * + query expansion) or falls back to `/predict` if the captioner isn't available.
 * Reranking scores are then polled progressively via `/predict-status/{job_id}`.
 */
import { useState, useCallback } from 'react'
import logoUrl from '../../../../media/logo.png'
import UploadScreen from './components/UploadScreen'
import ReviewView from './components/ReviewView'
import { ProcessingDisplay } from './components/ProcessingDisplay'
import { mapApiKeywordProgressive } from './utils/keywordAdapters'
import { useRerankPolling } from './hooks/useRerankPolling'

/** Backend base URL (override with `VITE_API_URL`). */
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export default function App() {
  const [phase, setPhase] = useState('upload')
  const [results, setResults] = useState([])
  const [resultIndex, setResultIndex] = useState(0)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingPreviewUrl, setProcessingPreviewUrl] = useState('')
  const [processingLabel, setProcessingLabel] = useState('')
  const [processingDescription, setProcessingDescription] = useState('')
  const [descriptionDone, setDescriptionDone] = useState(false)
  const [processingStatus, setProcessingStatus] = useState('')
  const [batchError, setBatchError] = useState('')

  /** Revokes blob URLs created for result thumbnails (call before discarding rows). */
  const revokeResultUrls = useCallback((list) => {
    list.forEach((r) => {
      if (r.previewUrl) URL.revokeObjectURL(r.previewUrl)
    })
  }, [])

  /**
   * Poll update: merge new scores into existing keywords while preserving
   * the user's `selected` state (match by keyword text).
   */
  const handlePollUpdate = useCallback((resultIdx, data) => {
    setResults((prev) => {
      const copy = [...prev]
      const row = copy[resultIdx]
      if (row?.type !== 'success') return prev

      const existing = row.keywords
      const updatedKeywords = (data.keywords || [])
        .map(mapApiKeywordProgressive)
        .filter((k) => k.text)
        .map((mapped) => {
          const match = existing.find((e) => e.text === mapped.text)
          return {
            ...mapped,
            selected: match ? match.selected : true,
          }
        })

      copy[resultIdx] = {
        ...row,
        keywords: updatedKeywords,
        rerankProgress: {
          completed: data.completed,
          total: data.total,
          status: data.status,
        },
      }
      return copy
    })
  }, [])

  const handlePollComplete = useCallback((resultIdx, data) => {
    setResults((prev) => {
      const copy = [...prev]
      const row = copy[resultIdx]
      if (row?.type !== 'success') return prev

      const existing = row.keywords
      const finalKeywords = (data.keywords || [])
        .map(mapApiKeywordProgressive)
        .filter((k) => k.text)
        .map((mapped) => {
          const match = existing.find((e) => e.text === mapped.text)
          return {
            ...mapped,
            selected: match ? match.selected : true,
          }
        })

      copy[resultIdx] = {
        ...row,
        keywords: finalKeywords,
        rerankProgress: {
          completed: data.total,
          total: data.total,
          status: 'done',
        },
      }
      return copy
    })
  }, [])

  const handlePollError = useCallback((resultIdx, errorMsg) => {
    setResults((prev) => {
      const copy = [...prev]
      const row = copy[resultIdx]
      if (row?.type !== 'success') return prev
      copy[resultIdx] = {
        ...row,
        rerankProgress: {
          ...row.rerankProgress,
          status: 'error',
          error: errorMsg,
        },
      }
      return copy
    })
  }, [])

  const { startPolling, stopAll } = useRerankPolling(
    API_URL,
    handlePollUpdate,
    handlePollComplete,
    handlePollError,
  )

  /**
   * Process a single file via the streaming endpoint.
   * Returns { resultData, description } on success, or null on SSE-level failure.
   *
   * @param {FormData} formData
   * @param {(t: number) => void} [onWithinFileProgress] Monotonic 0–1 progress for the
   *   current file only; parent maps this into overall batch percentage.
   */
  const processFileStream = async (formData, onWithinFileProgress) => {
    const res = await fetch(`${API_URL}/predict-stream`, {
      method: 'POST',
      headers: { 'ngrok-skip-browser-warning': 'true' },
      body: formData,
    })

    // 503 = captioner not loaded → caller should fall back to /predict
    if (res.status === 503) return null

    if (!res.ok) throw new Error(`Server error: ${res.status}`)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let resultData = null
    let descriptionChunks = ''
    let fullDescription = null
    let buffer = ''
    let sliceT = 0
    const bumpSlice = (t) => {
      const next = Math.max(sliceT, Math.min(1, t))
      if (next <= sliceT) return
      sliceT = next
      onWithinFileProgress?.(next)
    }

    bumpSlice(0.04)

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      // Keep the last potentially incomplete line in the buffer
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = line.slice(6).trim()
        if (payload === '[DONE]') continue
        try {
          const msg = JSON.parse(payload)
          if (msg.type === 'description') {
            descriptionChunks += msg.token
            setProcessingDescription((prev) => prev + msg.token)
            bumpSlice(0.06 + Math.min(0.72, descriptionChunks.length / 3500))
          } else if (msg.type === 'description_done') {
            if (typeof msg.full === 'string') fullDescription = msg.full
            setDescriptionDone(true)
            bumpSlice(0.86)
          } else if (msg.type === 'status') {
            setProcessingStatus(msg.message)
            bumpSlice(sliceT + 0.04)
          } else if (msg.type === 'result') {
            resultData = msg
            bumpSlice(0.96)
          } else if (msg.type === 'error') {
            throw new Error(msg.message)
          }
        } catch (parseErr) {
          // Skip malformed SSE lines
          if (parseErr.message && !parseErr.message.includes('JSON')) throw parseErr
        }
      }
    }

    return { resultData, description: (fullDescription ?? descriptionChunks).trim() }
  }

  /**
   * Process a single file via the non-streaming endpoint.
   */
  const processFileFallback = async (formData) => {
    const res = await fetch(`${API_URL}/predict`, {
      method: 'POST',
      headers: { 'ngrok-skip-browser-warning': 'true' },
      body: formData,
    })
    if (!res.ok) throw new Error(`Server error: ${res.status}`)
    const data = await res.json()
    return { job_id: data.job_id, keywords: data.keywords }
  }

  /**
   * Sequentially uploads each file, using `/predict-stream` (SSE with VLM
   * description) when available, falling back to `/predict` otherwise.
   *
   * @param {File[]} files
   * @param {number|object} termCountOrMap
   * @param {number} [lambdaMult]
   * @param {number} [queryBias]
   */
  const handleRequestProcess = async (files, termCountOrMap = 20, lambdaMult, queryBias) => {
    if (!files.length) return
    setBatchError('')
    setPhase('processing')
    setProcessingProgress(0)
    setProcessingPreviewUrl('')
    setProcessingDescription('')
    setDescriptionDone(false)
    setProcessingStatus('')
    const acc = []

    const isPerHierarchy =
      typeof termCountOrMap === 'object' && termCountOrMap !== null

    const clampedTermCount = isPerHierarchy
      ? null
      : (() => {
          const n = Number(termCountOrMap)
          if (!Number.isFinite(n)) return 20
          return Math.max(1, Math.min(50, Math.round(n)))
        })()

    // Track whether streaming is available (discovered on first file)
    let streamAvailable = true

    const fileWeight = files.length > 0 ? 100 / files.length : 100

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const previewUrl = URL.createObjectURL(file)
      setProcessingPreviewUrl(previewUrl)
      setProcessingLabel(`Processing image ${i + 1} of ${files.length}`)
      setProcessingDescription('')
      setDescriptionDone(false)
      setProcessingStatus('')

      const withinFile = (t) => {
        const clamped = Math.max(0, Math.min(1, t))
        setProcessingProgress(i * fileWeight + fileWeight * clamped)
      }
      withinFile(0.02)

      try {
        const formData = new FormData()
        formData.append('file', file)
        if (isPerHierarchy) {
          formData.append('hierarchy_counts', JSON.stringify(termCountOrMap))
        } else {
          formData.append('term_count', String(clampedTermCount))
        }
        if (lambdaMult !== undefined && lambdaMult !== null) {
          formData.append('lambda_mult', String(lambdaMult))
        }
        if (queryBias !== undefined && queryBias !== null) {
          formData.append('query_bias', String(queryBias))
        }

        let resultData = null
        let streamDescription = ''

        // Try streaming endpoint first
        if (streamAvailable) {
          const stream = await processFileStream(formData, withinFile)
          if (stream === null) {
            // Captioner not available — fall back for this and all subsequent files
            streamAvailable = false
          } else {
            resultData = stream.resultData
            streamDescription = stream.description || ''
          }
        }

        // Fall back to non-streaming endpoint
        if (!resultData) {
          withinFile(0.08)
          // Need a fresh FormData since the stream may have consumed the first one
          const fallbackForm = new FormData()
          fallbackForm.append('file', file)
          if (isPerHierarchy) {
            fallbackForm.append('hierarchy_counts', JSON.stringify(termCountOrMap))
          } else {
            fallbackForm.append('term_count', String(clampedTermCount))
          }
          if (lambdaMult !== undefined && lambdaMult !== null) {
            fallbackForm.append('lambda_mult', String(lambdaMult))
          }
          resultData = await processFileFallback(fallbackForm)
          withinFile(1)
        }

        acc.push({
          type: 'success',
          file,
          previewUrl,
          description: streamDescription,
          retrievalStats: resultData.retrieval_stats || null,
          keywords: (resultData.keywords || [])
            .map(mapApiKeywordProgressive)
            .filter((k) => k.text),
          jobId: resultData.job_id,
          rerankProgress: {
            completed: 0,
            total: (resultData.keywords || []).length,
            status: 'reranking',
          },
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

    // Start polling for each successful result's reranking progress
    ok.forEach((result) => {
      const actualIdx = acc.indexOf(result)
      startPolling(result.jobId, actualIdx)
    })
  }

  /** Clears results, revokes preview URLs, stops polling, and returns to the upload phase. */
  const handleUploadNew = () => {
    stopAll()
    revokeResultUrls(results)
    setResults([])
    setResultIndex(0)
    setPhase('upload')
    setBatchError('')
  }

  /**
   * Persists edited keywords for one successful result row (ReviewView).
   * @param {number} idx
   * @param {Array<{ text: string, confidence: number|null, [key: string]: unknown }>} nextKeywords
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
      <main className="mx-auto flex w-full flex-1 flex-col px-4 py-6 sm:px-8">
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
              description={processingDescription}
              descriptionDone={descriptionDone}
              processingStatus={processingStatus}
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
