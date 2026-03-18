import { useState, useRef } from 'react'
import NavBar from './NavBar'

export default function UploadScreen({ onProcessed }) {
  const [files, setFiles] = useState([])
  const [previewIndex, setPreviewIndex] = useState(0)
  const [status, setStatus] = useState('')
  const inputRef = useRef()

  const handleFiles = (incoming) => {
    const arr = Array.from(incoming)
    setFiles(arr)
    setPreviewIndex(0)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    handleFiles(e.dataTransfer.files)
  }

  const previewUrl = files.length > 0
    ? URL.createObjectURL(files[previewIndex])
    : null

  // Replace this URL each time you restart the Colab
  const API_URL = 'https://stilliform-celine-plaintively.ngrok-free.dev'

  const handleProcess = async () => {
    if (files.length === 0) return
    setStatus('Processing...')

    try {
      const results = []

      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)

        const res = await fetch(`${API_URL}/predict`, {
          method: 'POST',
          headers: { 'ngrok-skip-browser-warning': 'true' },
          body: formData,
        })

        if (!res.ok) throw new Error(`Server error: ${res.status}`)

        const data = await res.json()

        results.push({
          file,
          previewUrl: URL.createObjectURL(file),
          keywords: data.keywords.map(kw => ({ ...kw, selected: true })),
        })
      }

      setStatus('')
      onProcessed(results)
    } catch (err) {
      console.error(err)
      setStatus('Error connecting to backend. Is the Colab running?')
    }
  }

  return (
    <div>
      <div className="image-viewer">
        {previewUrl
          ? <img src={previewUrl} alt="preview" />
          : <span className="placeholder">No image selected</span>
        }
      </div>

      <NavBar
        current={previewIndex}
        total={files.length}
        onPrev={() => setPreviewIndex(i => Math.max(i - 1, 0))}
        onNext={() => setPreviewIndex(i => Math.min(i + 1, files.length - 1))}
      />

      <div
        className="upload-area"
        onClick={() => inputRef.current.click()}
        onDrop={handleDrop}
        onDragOver={e => e.preventDefault()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={e => handleFiles(e.target.files)}
        />
        <div className="upload-icon">↑</div>
        <p>Drop images here — or click to upload</p>
      </div>

      <button
        className="btn-primary"
        onClick={handleProcess}
        disabled={files.length === 0}
      >
        Generate Keywords
      </button>

      <div className="status">{status}</div>
    </div>
  )
}