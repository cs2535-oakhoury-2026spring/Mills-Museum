import { motion } from 'motion/react'
import { useState } from 'react'
import { ZoomIn, Copy, Check, FileText, Search } from 'lucide-react'
import { ImageModal } from './ImageModal'
import { isKeywordIncluded } from '../../utils/keywordAdapters'
import { reviewActionButtonSm } from '../../utils/reviewActionStyles'

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
    <div className="mx-auto w-full max-w-6xl min-w-0">
      <div className="grid min-w-0 gap-5 xl:grid-cols-12 xl:gap-6">
        <div className="min-w-0 max-w-full shrink-0 xl:col-span-4">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto w-full max-w-sm min-w-0 rounded-xl bg-slate-800 p-4 ring-1 ring-slate-700 xl:mx-0 xl:max-w-none xl:sticky xl:top-4"
          >
            <div className="mx-auto w-full max-w-sm min-w-0 overflow-hidden">
              <div className="group relative h-56 min-h-56 w-full min-w-0 overflow-hidden rounded-lg bg-slate-900/70">
                {imageSrc ? (
                  <img
                    src={imageSrc}
                    alt=""
                    className="absolute left-1/2 top-1/2 max-h-full max-w-full -translate-x-1/2 -translate-y-1/2 object-contain"
                  />
                ) : null}
                <button
                  type="button"
                  onClick={() => setIsModalOpen(true)}
                  disabled={!imageSrc}
                  className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100 disabled:pointer-events-none disabled:opacity-0"
                  aria-label="Enlarge image"
                >
                  <ZoomIn className="h-7 w-7 text-white" />
                </button>
              </div>
            </div>
            <p
              className="mt-3 break-all text-center text-xs text-slate-300"
              title={fileName}
            >
              {fileName}
            </p>
            <p className="mt-2 text-center text-xs text-slate-400">
              {included.length} of {keywords.length} keywords included for export
            </p>
          </motion.div>
        </div>

        <div className="min-w-0 xl:col-span-8">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="flex min-h-[280px] flex-col rounded-xl bg-slate-800 p-4 ring-1 ring-slate-700"
          >
            <div className="mb-3 flex flex-wrap items-start gap-3 border-b border-slate-700/80 pb-3">
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-medium text-slate-100">Keywords</h3>
                <p className="mt-0.5 text-xs text-slate-300">
                  Use the checkbox or click a tile. Long labels show fully on hover. Unchecked keywords are greyed and omitted from copy and exports.
                </p>
              </div>
              <div className="ms-auto flex shrink-0 flex-wrap justify-end gap-2">
                <button
                  type="button"
                  onClick={handleCopyKeywords}
                  disabled={included.length === 0}
                  className={reviewActionButtonSm}
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  type="button"
                  onClick={handleExportText}
                  disabled={included.length === 0}
                  className={reviewActionButtonSm}
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
                className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400"
                aria-hidden
              />
              <input
                id="kw-search"
                type="text"
                placeholder="Filter list…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md bg-slate-900/80 py-2 pl-8 pr-3 text-sm text-slate-100 ring-1 ring-slate-600 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/70"
              />
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto rounded-md bg-slate-900/40 p-2 ring-1 ring-slate-700/50">
              <div className="grid grid-cols-2 gap-1.5 content-start">
                {filteredWithIndex.map(({ k: keyword, i: globalIndex }) => {
                  const on = isKeywordIncluded(keyword)
                  const inputId = `kw-include-${globalIndex}`
                  return (
                    <motion.label
                      key={`${keyword.text}-${globalIndex}`}
                      htmlFor={inputId}
                      title={keyword.text}
                      initial={false}
                      animate={{ opacity: 1, scale: 1 }}
                      className={`flex min-w-0 cursor-pointer flex-col gap-0.5 rounded-md px-1.5 py-1 text-left transition-colors ${
                        on
                          ? 'bg-amber-500 text-slate-900 ring-1 ring-amber-600 hover:bg-amber-400'
                          : 'bg-slate-700/90 text-slate-300 ring-1 ring-slate-600 saturate-[0.88] hover:bg-slate-600 hover:saturate-100'
                      }`}
                    >
                      <div className="flex min-w-0 items-start gap-1.5">
                        <input
                          id={inputId}
                          type="checkbox"
                          checked={on}
                          onChange={() => toggleKeyword(globalIndex)}
                          className={`mt-0.5 h-4 w-4 shrink-0 cursor-pointer rounded border-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-amber-300 ${
                            on
                              ? 'border-slate-900/50 bg-amber-50 accent-amber-800'
                              : 'border-slate-400 bg-slate-800 accent-amber-600'
                          }`}
                          aria-label={
                            on
                              ? `${keyword.text}, included for export. Uncheck to exclude.`
                              : `${keyword.text}, excluded from export. Check to include.`
                          }
                        />
                        <span className="min-w-0 flex-1 leading-snug">
                          <span
                            className={`line-clamp-2 break-words text-sm font-medium ${
                              on ? 'text-slate-900' : 'text-slate-200'
                            }`}
                            title={keyword.text}
                          >
                            {keyword.text}
                          </span>
                        </span>
                      </div>
                      <span
                        className={`pl-[22px] text-xs font-normal tabular-nums leading-none ${
                          on ? 'text-slate-800' : 'text-slate-300'
                        }`}
                      >
                        {keyword.confidence}%
                      </span>
                    </motion.label>
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
