import { useState } from 'react'
import UploadScreen from './components/UploadScreen'
import ReviewScreen from './components/ReviewScreen'

export default function App() {
  const [results, setResults] = useState(null)

  return (
    <div className="app">
      <h1>MCAM Art Keyword Generator</h1>
      <p className="subtitle">
        Upload artwork images to automatically generate AAT keywords for cataloging.
      </p>

      {results === null
        ? <UploadScreen onProcessed={setResults} />
        : <ReviewScreen results={results} onUploadNew={() => setResults(null)} />
      }
    </div>
  )
}