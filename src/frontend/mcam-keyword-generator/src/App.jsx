import { useState, useCallback } from 'react'
import logoUrl from '../../../../media/inverted color logo.png'
import UploadScreen from './components/UploadScreen'
import ReviewView from './components/ReviewView'
import { ProcessingDisplay } from './components/figma/ProcessingDisplay'
import { mapApiKeyword } from './utils/keywordAdapters'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [phase, setPhase] = useState('upload')
  const [results, setResults] = useState([])
  const [resultIndex, setResultIndex] = useState(0)
  const [processingProgress, setProcessingProgress] = useState(0)
  const [processingPreviewUrl, setProcessingPreviewUrl] = useState('')
  const [processingLabel, setProcessingLabel] = useState('')
  const [batchError, setBatchError] = useState('')

  const revokeResultUrls = useCallback((list) => {
    list.forEach((r) => {
      if (r.previewUrl) URL.revokeObjectURL(r.previewUrl)
    })
  }, [])

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

  const handleUploadNew = () => {
    revokeResultUrls(results)
    setResults([])
    setResultIndex(0)
    setPhase('upload')
    setBatchError('')
  }

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
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      <header className="sticky top-0 z-30 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <img
              src={logoUrl}
              alt="Mills College Art Museum"
              className="h-9 w-auto max-w-[200px] object-contain object-left"
            />
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-white">
                MCAM Keyword Generator
              </h1>
              <p className="text-xs text-slate-400">Art & Architecture Thesaurus Pipeline</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 ring-1 ring-emerald-500/20">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              {phase === 'upload'
                ? 'Ready'
                : phase === 'processing'
                  ? 'Processing'
                  : 'Review'}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-8 sm:px-6 sm:py-10">
        {phase === 'upload' ? (
          <div className="mb-8 text-center">
            <h2 className="text-xl font-medium text-slate-50 sm:text-2xl">
              MCAM Art Keyword Generator
            </h2>
            <p className="mcam-subtitle mx-auto mt-2 max-w-2xl text-slate-400">
              Upload artwork images to automatically generate AAT keywords for
              cataloging.
            </p>
          </div>
        ) : null}

        <div className="flex w-full min-w-0 flex-1 justify-center">
          {phase === 'upload' ? (
            <div className="mx-auto w-full min-w-0 max-w-6xl shrink-0">
              <UploadScreen
                onRequestProcess={handleRequestProcess}
                errorMessage={batchError}
                onDismissError={() => setBatchError('')}
              />
            </div>
          ) : null}

          {phase === 'processing' ? (
            <ProcessingDisplay
              progress={processingProgress}
              imageSrc={processingPreviewUrl}
              keywords={[]}
              statusLabel={processingLabel}
            />
          ) : null}

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

      <footer className="border-t border-slate-800/60 bg-slate-950/60 py-4 text-center text-xs text-slate-500">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          AAT keyword pipeline
        </div>
      </footer>
    </div>
  )
}
