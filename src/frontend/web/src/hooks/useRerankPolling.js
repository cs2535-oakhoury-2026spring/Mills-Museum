import { useRef, useCallback } from 'react'

/**
 * Poll cadence: fast enough that the progress bar feels responsive, slow enough
 * to avoid hammering Colab / a single-worker API. Adjust here if the backend
 * rate-limits or if jobs are very long.
 */
const POLL_INTERVAL_MS = 1500

/**
 * Network blips (sleeping laptop, ngrok hiccup) should not tear down polling
 * immediately. After this many consecutive failed fetches we assume the job
 * channel is gone and surface a user-visible error via `onError`.
 */
const MAX_CONSECUTIVE_FAILURES = 10

/**
 * Manages polling intervals for background reranking jobs.
 *
 * One interval per `jobId` so multiple images in a batch can rerank in parallel.
 * Refs store timer ids and per-job failure counts so callbacks stay stable and
 * we do not recreate intervals on unrelated parent re-renders.
 *
 * @param {string} apiUrl        Backend base URL
 * @param {Function} onUpdate    Called on each successful poll: (resultIndex, data)
 * @param {Function} onComplete  Called when job status is "done": (resultIndex, data)
 * @param {Function} onError     Called when job status is "error": (resultIndex, errorMsg)
 */
export function useRerankPolling(apiUrl, onUpdate, onComplete, onError) {
  const intervalsRef = useRef({})
  const failCountRef = useRef({})

  const startPolling = useCallback(
    (jobId, resultIndex) => {
      failCountRef.current[jobId] = 0

      const poll = async () => {
        try {
          const res = await fetch(`${apiUrl}/predict-status/${jobId}`, {
            headers: { 'ngrok-skip-browser-warning': 'true' },
          })
          if (!res.ok) throw new Error(`Status error: ${res.status}`)
          const data = await res.json()

          failCountRef.current[jobId] = 0
          onUpdate(resultIndex, data)

          if (data.status === 'done' || data.status === 'error') {
            clearInterval(intervalsRef.current[jobId])
            delete intervalsRef.current[jobId]
            delete failCountRef.current[jobId]
            if (data.status === 'done') onComplete(resultIndex, data)
            if (data.status === 'error') onError(resultIndex, data.error)
          }
        } catch (err) {
          console.warn('Rerank poll failed:', err)
          failCountRef.current[jobId] = (failCountRef.current[jobId] || 0) + 1
          if (failCountRef.current[jobId] >= MAX_CONSECUTIVE_FAILURES) {
            clearInterval(intervalsRef.current[jobId])
            delete intervalsRef.current[jobId]
            delete failCountRef.current[jobId]
            onError(resultIndex, 'Lost connection to backend during reranking.')
          }
        }
      }

      poll()
      intervalsRef.current[jobId] = setInterval(poll, POLL_INTERVAL_MS)
    },
    [apiUrl, onUpdate, onComplete, onError],
  )

  const stopAll = useCallback(() => {
    Object.values(intervalsRef.current).forEach(clearInterval)
    intervalsRef.current = {}
    failCountRef.current = {}
  }, [])

  return { startPolling, stopAll }
}
