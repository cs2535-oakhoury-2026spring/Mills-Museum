import { useState, useCallback } from 'react'
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

  const handleRequestProcess = async (files) => {
    if (!files.length) return
    setBatchError('')
    setPhase('processing')
    setProcessingProgress(0)
    setProcessingPreviewUrl('')
    const acc = []

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const previewUrl = URL.createObjectURL(file)
      setProcessingPreviewUrl(previewUrl)
      setProcessingLabel(`Processing image ${i + 1} of ${files.length}`)
      const t0 = performance.now()
      try {
        const formData = new FormData()
        formData.append('file', file)
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
    <div className="mcam-app min-h-screen bg-slate-950 px-4 py-10 text-slate-100">
      <div className="mx-auto max-w-6xl">
        <header className="mb-10 text-center">
          <h1 className="text-slate-50">MCAM Art Keyword Generator</h1>
          <p className="mcam-subtitle mt-2 max-w-2xl mx-auto text-slate-400">
            Upload artwork images to automatically generate AAT keywords for
            cataloging.
          </p>
        </header>

        <div className="flex w-full justify-center">
          {phase === 'upload' ? (
            <UploadScreen
              onRequestProcess={handleRequestProcess}
              errorMessage={batchError}
              onDismissError={() => setBatchError('')}
            />
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
            <div className="w-full">
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
      </div>
    </div>
  )
}
