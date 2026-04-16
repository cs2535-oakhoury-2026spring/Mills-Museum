import { motion } from 'motion/react'
import { useState } from 'react'
import { ZoomIn, Copy, Check, FileText, Search } from 'lucide-react'
import { ImageModal } from './ImageModal'
import {
  getAccessionNumberFromTitle,
  isKeywordIncluded,
  stripFileExtension,
  downloadTextFile,
} from '../utils/keywordAdapters'
import { getConfidenceBadgeStyle } from '../utils/confidenceBadgeStyle'
import { reviewActionButtonSm } from '../utils/reviewActionStyles'

/**
 * Per-image review panel.
 *
 * Keeps "real" review data (keywords + selection) controlled by the parent via
 * `keywords` + `onKeywordsChange`, while owning only transient UI state:
 * - copy feedback
 * - modal open/close
 * - search query
 */
export function ResultDisplay({
  imageSrc,
  keywords, // {text, confidence, selected}
  onKeywordsChange,
  fileName,
}) {
  const [copied, setCopied] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // A single definition of "included" keeps UI + copy/export behavior aligned.
  const included = keywords.filter(isKeywordIncluded)

  // Keep the original keyword index while filtering, so toggles update the correct
  // element in the source array (not the filtered slice).
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
    // Small UX touch: show "Copied" briefly without complicating global state.
    setTimeout(() => setCopied(false), 2000)
  }

  const toggleKeyword = (index) => {
    // Immutable update makes React state changes predictable.
    onKeywordsChange(
      keywords.map((k, i) =>
        i === index ? { ...k, selected: !isKeywordIncluded(k) } : k,
      ),
    )
  }

  const handleExportText = () => {
    const lines = included.map((k) => `  - ${k.text} (${k.confidence}%)`)
    const label = stripFileExtension(fileName) || 'keywords'
    const text = `${label}

Keywords (${included.length}):
${lines.join('\n')}

Comma-separated: ${included.map((k) => k.text).join(', ')}
`

    // Per-image export uses the same browser download pattern as the batch export.
    downloadTextFile(`${label}_keywords.txt`, text)
  }

  const handleExportCsv = () => {
    const accession = getAccessionNumberFromTitle(fileName) || 'unknown'
    const header = 'accession_number,keyword'
    const rows = included.map((k) => {
      const a = String(accession).replace(/"/g, '""')
      const kw = String(k.text).replace(/"/g, '""')
      const accCell = /[",\n\r]/.test(a) ? `"${a}"` : a
      const kwCell = /[",\n\r]/.test(kw) ? `"${kw}"` : kw
      return `${accCell},${kwCell}`
    })
    downloadTextFile(`${accession}_keywords.csv`, [header, ...rows].join('\n'))
  }

  return (
    <div className="mx-auto w-full max-w-6xl min-w-0">
      {/* Two-column responsive layout: image summary (left) and keyword review (right). */}
      <div className="grid min-w-0 gap-5 xl:grid-cols-12 xl:gap-6">
        {/* Left column: image preview card and per-image inclusion summary. */}
        <div className="min-w-0 max-w-full shrink-0 xl:col-span-4">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto w-full max-w-sm min-w-0 rounded-xl border-2 border-mcam-navy/20 bg-white p-4 shadow-sm xl:mx-0 xl:max-w-none xl:sticky xl:top-4"
          >
            <div className="mx-auto w-full max-w-sm min-w-0 overflow-hidden">
              {/* Preview frame with hover-to-zoom overlay trigger. */}
              <div className="group relative h-56 min-h-56 w-full min-w-0 overflow-hidden rounded-lg border border-mcam-navy/15 bg-mcam-surface">
                {imageSrc ? (
                  <img
                    src={imageSrc}
                    alt=""
                    className="absolute inset-0 box-border h-full w-full max-h-full max-w-full object-contain object-center p-2"
                  />
                ) : null}
                {/* Full-frame button opens modal with enlarged image. */}
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
              className="mt-3 break-all text-center text-xs text-mcam-navy"
              title={fileName}
            >
              {fileName}
            </p>
            {/* Inclusion summary used for copy/export actions below. */}
            <p className="mt-2 text-center text-xs text-mcam-muted">
              {included.length} of {keywords.length} keywords included for export
            </p>
          </motion.div>
        </div>

        {/* Right column: keyword tools (copy/export/filter) and selectable keyword list. */}
        <div className="min-w-0 xl:col-span-8">
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="flex min-h-[280px] flex-col rounded-xl border-2 border-mcam-navy/20 bg-white p-4 shadow-sm"
          >
            {/* Top row: panel title/help text and keyword action buttons. */}
            <div className="mb-3 flex flex-wrap items-start gap-3 border-b-2 border-mcam-navy/15 pb-3">
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-medium text-mcam-navy">Keywords</h3>
                <p className="mt-0.5 text-xs text-mcam-muted">
                  Use the checkbox or click a tile. Long labels show fully on hover. Unchecked keywords are greyed and omitted from copy and exports.
                </p>
              </div>
              {/* Actions apply only to currently included keywords. */}
              <div className="ms-auto flex shrink-0 flex-wrap justify-end gap-2">
                {/* Copies included keywords as comma-separated text. */}
                <button
                  type="button"
                  onClick={handleCopyKeywords}
                  disabled={included.length === 0}
                  className={reviewActionButtonSm}
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                {/* Exports this image's included keywords to TXT. */}
                <button
                  type="button"
                  onClick={handleExportText}
                  disabled={included.length === 0}
                  className={reviewActionButtonSm}
                >
                  <FileText className="h-3.5 w-3.5" />
                  TXT
                </button>
                {/* Exports this image's included keywords to CSV. */}
                <button
                  type="button"
                  onClick={handleExportCsv}
                  disabled={included.length === 0}
                  className={reviewActionButtonSm}
                >
                  CSV
                </button>
              </div>
            </div>

            {/* Accessible label for the keyword filter input. */}
            <label className="sr-only" htmlFor="kw-search">
              Search keywords
            </label>
            {/* Client-side keyword filter input with search icon affordance. */}
            <div className="relative mb-3">
              <Search
                className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-mcam-muted"
                aria-hidden
              />
              <input
                id="kw-search"
                type="text"
                placeholder="Filter list…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border-2 border-mcam-navy/20 bg-white py-2 pl-8 pr-3 text-sm text-mcam-navy placeholder:text-mcam-muted focus:border-mcam-blue focus:outline-none"
              />
            </div>

            {/* Scrollable keyword tile list; each tile toggles inclusion for export. */}
            <div className="min-h-0 flex-1 overflow-y-auto rounded-md border border-mcam-navy/15 bg-mcam-surface p-2.5">
              <div className="grid grid-cols-2 gap-2 content-start">
                {filteredWithIndex.map(({ k: keyword, i: globalIndex }) => {
                  const on = isKeywordIncluded(keyword)
                  const inputId = `kw-include-${globalIndex}`
                  return (
                    /* Tile is a label so clicking anywhere toggles its hidden checkbox. */
                    <motion.label
                      key={`${keyword.text}-${globalIndex}`}
                      htmlFor={inputId}
                      title={keyword.text}
                      initial={false}
                      animate={{ opacity: 1, scale: 1 }}
                      className={`inline-flex w-full min-w-0 cursor-pointer items-center gap-2 rounded-md border border-[#2f5a94]/60 bg-[#3b6db5] px-3 py-2 text-left text-xs font-semibold !text-white shadow-sm transition hover:brightness-105 focus-within:brightness-105 ${
                        on
                          ? 'ring-2 ring-white/90 ring-offset-2 ring-offset-mcam-surface'
                          : ''
                      }`}
                    >
                      {/* Screen-reader checkbox control that drives include/exclude state. */}
                      <input
                        id={inputId}
                        type="checkbox"
                        checked={on}
                        onChange={() => toggleKeyword(globalIndex)}
                        className="peer sr-only"
                        aria-label={
                          on
                            ? `${keyword.text}, included for export. Uncheck to exclude.`
                            : `${keyword.text}, excluded from export. Check to include.`
                        }
                      />
                      {/* Visual checkmark indicator synced with checkbox state. */}
                      <span
                        aria-hidden
                        className="mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded border-2 border-white/95 bg-white/92 shadow-md peer-checked:border-[#93c5fd]/70 peer-checked:bg-[#2f5a94]/95 peer-focus-visible:ring-1 peer-focus-visible:ring-white/50 peer-focus-visible:ring-offset-1 peer-focus-visible:ring-offset-[#3b6db5] [&_svg]:opacity-0 peer-checked:[&_svg]:opacity-100"
                      >
                        <Check
                          className="h-3 w-3 text-white"
                          strokeWidth={2.5}
                        />
                      </span>
                      {/* Keyword text, line-clamped for compact tile layout. */}
                      <span className="min-w-0 flex-1 leading-snug">
                        <span
                          className="line-clamp-2 break-words text-sm font-semibold leading-snug text-white sm:text-base"
                          title={keyword.text}
                        >
                          {keyword.text}
                        </span>
                      </span>
                      {/* Confidence badge styled by confidence score bucket. */}
                      <span
                        className="inline-flex min-w-[2.75rem] shrink-0 items-center justify-center self-center rounded-md border border-solid px-1.5 py-0.5 text-[11px] font-bold tabular-nums leading-none shadow-sm"
                        style={getConfidenceBadgeStyle(keyword.confidence)}
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

      {/* Controlled modal: ResultDisplay owns only the open/close UI state */}
      <ImageModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        imageSrc={imageSrc}
        fileName={fileName}
      />
    </div>
  )
}
