import { motion, AnimatePresence } from 'motion/react'
import { useState, useEffect, useRef } from 'react'
import { ZoomIn, Copy, Check, FileText, Search, ChevronDown, Layers } from 'lucide-react'
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
 * - scope note expansion
 * - hierarchy grouping toggle
 */
export function ResultDisplay({
  imageSrc,
  keywords, // {text, confidence, selected, scopeNote, hierarchy}
  onKeywordsChange,
  fileName,
  rerankProgress,
}) {
  const [copied, setCopied] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedIndex, setExpandedIndex] = useState(null)
  const [groupByHierarchy, setGroupByHierarchy] = useState(false)

  // Reset transient UI state when the image changes
  const prevFileNameRef = useRef(fileName)
  useEffect(() => {
    if (prevFileNameRef.current !== fileName) {
      prevFileNameRef.current = fileName
      setSearchQuery('')
      setCopied(false)
      setIsModalOpen(false)
      setExpandedIndex(null)
    }
  }, [fileName])

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
    const lines = included.map((k) =>
      k.confidence !== null ? `  - ${k.text} (${k.confidence}%)` : `  - ${k.text}`,
    )
    const label = stripFileExtension(fileName) || 'keywords'
    const text = `${label}

Keywords (${included.length}):
${lines.join('\n')}

Comma-separated: ${included.map((k) => k.text).join(', ')}
`
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

  /** Renders a single keyword tile with optional scope note dropdown. */
  const renderKeywordTile = ({ k: keyword, i: globalIndex }) => {
    const on = isKeywordIncluded(keyword)
    const inputId = `kw-include-${globalIndex}`
    const hasScopeNote = Boolean(keyword.scopeNote)
    const isExpanded = expandedIndex === globalIndex

    return (
      <div key={`${globalIndex}-${keyword.text}`} className="flex flex-col">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
          className={`inline-flex w-full min-w-0 items-center gap-1.5 rounded border border-[#2f5a94]/50 bg-[#3b6db5] px-2 py-1.5 text-left text-white shadow-sm transition hover:brightness-110 ${
            on
              ? 'ring-1 ring-white/80 ring-offset-1 ring-offset-mcam-surface'
              : 'opacity-60'
          } ${isExpanded ? 'rounded-b-none' : ''}`}
        >
          {/* Checkbox area — click target for toggling inclusion */}
          <label htmlFor={inputId} className="flex shrink-0 cursor-pointer items-center">
            <input
              id={inputId}
              type="checkbox"
              checked={on}
              onChange={() => toggleKeyword(globalIndex)}
              className="peer sr-only"
              aria-label={
                on
                  ? `${keyword.text}, included. Uncheck to exclude.`
                  : `${keyword.text}, excluded. Check to include.`
              }
            />
            <span
              aria-hidden
              className="flex h-3.5 w-3.5 items-center justify-center rounded-sm border border-white/80 bg-white/85 peer-checked:border-[#93c5fd]/60 peer-checked:bg-[#2f5a94]/90 [&_svg]:opacity-0 peer-checked:[&_svg]:opacity-100"
            >
              <Check className="h-2.5 w-2.5 text-white" strokeWidth={3} />
            </span>
          </label>
          {/* Keyword text */}
          <span
            className="min-w-0 flex-1 truncate text-xs font-medium leading-tight text-white"
            title={keyword.text}
          >
            {keyword.text}
          </span>
          {/* Confidence badge */}
          <span
            className="inline-flex min-w-[2rem] shrink-0 items-center justify-center rounded border border-solid px-1 py-px text-[10px] font-bold tabular-nums leading-none"
            style={
              keyword.confidence !== null
                ? getConfidenceBadgeStyle(keyword.confidence)
                : {
                    background: 'rgba(255,255,255,0.5)',
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: '#64748b',
                  }
            }
          >
            {keyword.confidence !== null ? (
              `${keyword.confidence}%`
            ) : (
              <span className="animate-pulse">&hellip;</span>
            )}
          </span>
          {/* Scope note toggle — only shown when a note exists */}
          {hasScopeNote ? (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setExpandedIndex(isExpanded ? null : globalIndex)
              }}
              className="ml-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded hover:bg-white/20 transition-colors"
              aria-label={isExpanded ? 'Hide scope note' : 'Show scope note'}
              title="Scope note"
            >
              <ChevronDown
                className={`h-3 w-3 text-white/80 transition-transform duration-150 ${isExpanded ? 'rotate-180' : ''}`}
              />
            </button>
          ) : null}
        </motion.div>
        {/* Scope note dropdown */}
        <AnimatePresence>
          {isExpanded && hasScopeNote ? (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="overflow-hidden"
            >
              <div className="rounded-b border border-t-0 border-[#2f5a94]/30 bg-[#2a5a9e] px-2.5 py-2 text-[11px] leading-relaxed text-white/90">
                {keyword.scopeNote}
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>
    )
  }

  /** Builds grouped sections when hierarchy view is active. */
  const renderGroupedKeywords = () => {
    const groups = {}
    for (const item of filteredWithIndex) {
      const h = item.k.hierarchy || 'Other'
      if (!groups[h]) groups[h] = []
      groups[h].push(item)
    }
    const sortedHierarchies = Object.keys(groups).sort()

    return sortedHierarchies.map((hierarchy) => (
      <div key={hierarchy}>
        <div className="sticky top-0 z-10 mb-1 rounded bg-mcam-navy/10 px-2 py-1">
          <span className="text-[11px] font-semibold text-mcam-navy/70">
            {hierarchy}
          </span>
          <span className="ml-1.5 text-[10px] text-mcam-muted">
            ({groups[hierarchy].length})
          </span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 content-start lg:grid-cols-3 mb-2">
          {groups[hierarchy].map(renderKeywordTile)}
        </div>
      </div>
    ))
  }

  return (
    <div className="w-full min-w-0">
      {/* Side-by-side layout: image (left) + keywords (right) */}
      <div className="grid min-w-0 gap-4 lg:grid-cols-12">
        {/* Left column: large image preview */}
        <div className="min-w-0 lg:col-span-5">
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-mcam-navy/15 bg-white p-3 shadow-sm lg:sticky lg:top-16"
          >
            {/* Image preview — taller to show artwork properly */}
            <div className="group relative aspect-[4/3] w-full min-w-0 overflow-hidden rounded-md border border-mcam-navy/10 bg-mcam-surface">
              {imageSrc ? (
                <img
                  src={imageSrc}
                  alt=""
                  className="absolute inset-0 box-border h-full w-full max-h-full max-w-full object-contain object-center p-2"
                />
              ) : null}
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                disabled={!imageSrc}
                className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100 disabled:pointer-events-none disabled:opacity-0"
                aria-label="Enlarge image"
              >
                <ZoomIn className="h-6 w-6 text-white" />
              </button>
            </div>
            <div className="mt-2 flex items-center justify-between gap-2">
              <p
                className="min-w-0 truncate text-xs text-mcam-navy"
                title={fileName}
              >
                {fileName}
              </p>
              <p className="shrink-0 text-[11px] text-mcam-muted">
                {included.length}/{keywords.length} included
              </p>
            </div>
          </motion.div>
        </div>

        {/* Right column: keyword tools + selectable keyword grid */}
        <div className="min-w-0 lg:col-span-7">
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="flex min-h-[300px] flex-col rounded-lg border border-mcam-navy/15 bg-white p-3 shadow-sm"
          >
            {/* Compact header: title + action buttons */}
            <div className="mb-2 flex items-center gap-2 border-b border-mcam-navy/10 pb-2">
              <h3 className="text-xs font-semibold text-mcam-navy">Keywords</h3>
              <div className="ms-auto flex shrink-0 gap-1.5">
                <button
                  type="button"
                  onClick={() => setGroupByHierarchy((v) => !v)}
                  className={`${reviewActionButtonSm} ${groupByHierarchy ? '!bg-[#2a4f8a] ring-1 ring-white/40' : ''}`}
                  title={groupByHierarchy ? 'Show flat list' : 'Group by hierarchy'}
                >
                  <Layers className="h-3 w-3" />
                  Group
                </button>
                <button
                  type="button"
                  onClick={handleCopyKeywords}
                  disabled={included.length === 0}
                  className={reviewActionButtonSm}
                >
                  {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  type="button"
                  onClick={handleExportText}
                  disabled={included.length === 0}
                  className={reviewActionButtonSm}
                >
                  <FileText className="h-3 w-3" />
                  TXT
                </button>
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

            {/* Reranking progress bar */}
            {rerankProgress && rerankProgress.status !== 'done' && (
              <div className="mb-2">
                <div className="flex items-center justify-between text-[11px] text-mcam-muted mb-0.5">
                  <span>
                    {rerankProgress.status === 'error'
                      ? 'Scoring interrupted'
                      : 'Scoring keywords\u2026'}
                  </span>
                  <span className="tabular-nums font-medium">
                    {rerankProgress.completed}/{rerankProgress.total}
                  </span>
                </div>
                <div className="h-1 w-full overflow-hidden rounded-full bg-mcam-surface border border-mcam-navy/10">
                  <motion.div
                    className={`h-full ${rerankProgress.status === 'error' ? 'bg-red-400' : 'bg-mcam-blue'}`}
                    animate={{
                      width: `${rerankProgress.total > 0 ? (rerankProgress.completed / rerankProgress.total) * 100 : 0}%`,
                    }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                  />
                </div>
              </div>
            )}

            {/* Search filter */}
            <label className="sr-only" htmlFor="kw-search">
              Search keywords
            </label>
            <div className="relative mb-2">
              <Search
                className="pointer-events-none absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-mcam-muted"
                aria-hidden
              />
              <input
                id="kw-search"
                type="text"
                placeholder="Filter\u2026"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded border border-mcam-navy/15 bg-white py-1.5 pl-7 pr-2 text-xs text-mcam-navy placeholder:text-mcam-muted focus:border-mcam-blue focus:outline-none"
              />
            </div>

            {/* Keyword grid */}
            <div className="min-h-0 flex-1 overflow-y-auto rounded border border-mcam-navy/10 bg-mcam-surface p-2">
              {groupByHierarchy ? (
                renderGroupedKeywords()
              ) : (
                <div className="grid grid-cols-2 gap-1.5 content-start lg:grid-cols-3">
                  {filteredWithIndex.map(renderKeywordTile)}
                </div>
              )}
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
