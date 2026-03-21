import { motion } from 'motion/react'
import { useState } from 'react'
import { ZoomIn, Copy, Check, FileText, Search } from 'lucide-react'
import { ImageModal } from './ImageModal'
import { isKeywordIncluded } from '../../utils/keywordAdapters'

export function ResultDisplay({
  imageSrc,
  keywords,
  onKeywordsChange,
  fileName,
}) {
  const [copied, setCopied] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const included = keywords.filter(isKeywordIncluded)

  const filteredWithIndex = keywords
    .map((k, i) => ({ k, i }))
    .filter(({ k }) => {
      const q = searchQuery.trim().toLowerCase()
      return q === '' || k.text.toLowerCase().includes(q)
    })

  const handleCopyKeywords = () => {
    const text = included.map((k) => k.text).join(', ')
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const toggleKeyword = (index) => {
    onKeywordsChange(
      keywords.map((k, i) =>
        i === index ? { ...k, selected: !isKeywordIncluded(k) } : k,
      ),
    )
  }

  const handleExportText = () => {
    const lines = included.map((k) => `  - ${k.text} (${k.confidence}%)`)
    const text = `${fileName}

Keywords (${included.length}):
${lines.join('\n')}

Comma-separated: ${included.map((k) => k.text).join(', ')}
`

    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const base = fileName.replace(/\.[^.]+$/, '') || 'keywords'
    a.download = `${base}_keywords.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="w-full">
      <div className="grid gap-5 xl:grid-cols-12 xl:gap-6">
        <div className="xl:col-span-4">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl bg-slate-800 p-4 ring-1 ring-slate-700 xl:sticky xl:top-4"
          >
            <div className="group relative overflow-hidden rounded-lg bg-slate-700">
              <img
                src={imageSrc}
                alt=""
                className="aspect-square w-full object-cover"
              />
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100"
                aria-label="Enlarge image"
              >
                <ZoomIn className="h-7 w-7 text-white" />
              </button>
            </div>
            <p
              className="mt-3 break-all text-center text-xs text-slate-400"
              title={fileName}
            >
              {fileName}
            </p>
            <p className="mt-2 text-center text-[11px] text-slate-500">
              {included.length} of {keywords.length} keywords included for export
            </p>
          </motion.div>
        </div>

        <div className="min-w-0 xl:col-span-8">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="flex h-full min-h-[280px] flex-col rounded-xl bg-slate-800 p-4 ring-1 ring-slate-700"
          >
            <div className="mb-3 flex flex-wrap items-start justify-between gap-3 border-b border-slate-700/80 pb-3">
              <div>
                <h3 className="text-sm font-medium text-slate-200">Keywords</h3>
                <p className="mt-0.5 text-xs text-slate-500">
                  Tap a keyword to grey it out — greyed terms are omitted from copy and exports.
                </p>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleCopyKeywords}
                  disabled={included.length === 0}
                  className="flex items-center gap-1.5 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-medium text-slate-900 transition-colors hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  type="button"
                  onClick={handleExportText}
                  disabled={included.length === 0}
                  className="flex items-center gap-1.5 rounded-md bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 ring-1 ring-slate-600 transition-colors hover:bg-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <FileText className="h-3.5 w-3.5" />
                  TXT
                </button>
              </div>
            </div>

            <label className="sr-only" htmlFor="kw-search">
              Search keywords
            </label>
            <div className="relative mb-3">
              <Search
                className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500"
                aria-hidden
              />
              <input
                id="kw-search"
                type="text"
                placeholder="Filter list…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md bg-slate-900/60 py-2 pl-8 pr-3 text-xs text-slate-200 ring-1 ring-slate-600 placeholder:text-slate-600 focus:outline-none focus:ring-amber-500/50"
              />
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto rounded-md bg-slate-900/40 p-3 ring-1 ring-slate-700/50">
              <div className="flex flex-wrap content-start gap-2">
                {filteredWithIndex.map(({ k: keyword, i: globalIndex }) => {
                  const on = isKeywordIncluded(keyword)
                  return (
                    <motion.button
                      key={`${keyword.text}-${globalIndex}`}
                      type="button"
                      initial={false}
                      animate={{ opacity: 1, scale: 1 }}
                      onClick={() => toggleKeyword(globalIndex)}
                      className={`max-w-full rounded-md px-2.5 py-1.5 text-left text-xs font-medium transition-colors ${
                        on
                          ? 'bg-amber-500 text-slate-900 hover:bg-amber-400'
                          : 'bg-slate-700/60 text-slate-500 ring-1 ring-slate-600 hover:bg-slate-700'
                      }`}
                      aria-pressed={on}
                      aria-label={
                        on
                          ? `${keyword.text}, included. Click to exclude.`
                          : `${keyword.text}, excluded. Click to include.`
                      }
                    >
                      <span className="break-words">{keyword.text}</span>
                      <span
                        className={`mt-0.5 block text-[10px] ${on ? 'text-slate-800/80' : 'text-slate-600'}`}
                      >
                        {keyword.confidence}%
                      </span>
                    </motion.button>
                  )
                })}
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      <ImageModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        imageSrc={imageSrc}
        fileName={fileName}
      />
    </div>
  )
}
