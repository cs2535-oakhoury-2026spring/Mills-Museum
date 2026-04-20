/**
 * Frontend adapter helpers.
 *
 * The backend can evolve independently from the UI. These functions normalize
 * backend-ish shapes into small, UI-friendly primitives so components can stay
 * focused on rendering and interaction.
 */
/**
 * Some API responses include human-readable definitions after the term.
 * The UI and exports only need the canonical term string.
 *
 * @param {unknown} rawText
 * @returns {string}
 */
function stripKeywordDefinition(rawText) {
  if (rawText == null) return ''
  const text = String(rawText).trim()
  if (!text) return ''

  // Your backend may sometimes return labels in the form:
  //   "<term> : <definition>"
  //   "<term> :"
  // We only want to display "<term>".
  const delimiter = ' : '
  if (text.includes(delimiter)) {
    return text.split(delimiter, 1)[0].trim()
  }

  if (text.endsWith(' :')) {
    return text.slice(0, -2).trim()
  }

  if (text.endsWith(':')) {
    return text.slice(0, -1).trim()
  }

  return text
}

/**
 * Accession number convention:
 * - start from the "title" (usually the filename without extension)
 * - if the title contains an underscore, ignore everything after the first `_`
 *
 * Examples:
 * - "ABC123_front" -> "ABC123"
 * - "M-001" -> "M-001"
 */
export function getAccessionNumberFromTitle(title) {
  const base = stripFileExtension(title)
  if (!base) return ''
  const head = base.split('_', 1)[0].trim()
  return head || base
}

/**
 * Maps raw API keywords (label/text + score) into the UI keyword model.
 * `selected` defaults true so results start in an "included" state.
 */
export function mapApiKeyword(kw) {
  const rawScore = kw.score
  const score =
    typeof rawScore === 'number' ? rawScore : parseFloat(rawScore)

  const rawText = kw.label ?? kw.text ?? ''

  return {
    text: stripKeywordDefinition(rawText),
    confidence: Number.isFinite(score) ? Math.round(score * 10) / 10 : 0,
    selected: true,
  }
}

/**
 * Progressive variant: returns `confidence: null` when the backend hasn't
 * scored the keyword yet (score is null/undefined). This signals the UI
 * to show a placeholder instead of "0%".
 */
export function mapApiKeywordProgressive(kw) {
  const rawScore = kw.score
  const hasScore = rawScore !== null && rawScore !== undefined
  const score = hasScore
    ? typeof rawScore === 'number'
      ? rawScore
      : parseFloat(rawScore)
    : null

  const rawText = kw.label ?? kw.text ?? ''

  return {
    text: stripKeywordDefinition(rawText),
    confidence:
      score !== null && Number.isFinite(score)
        ? Math.round(score * 10) / 10
        : null,
    selected: true,
    scopeNote: kw.scope_note ?? '',
    hierarchy: kw.hierarchy ?? '',
  }
}

/**
 * Keyword is included in exports when `selected` is not explicitly false.
 * This makes inclusion the default, even if older data lacks a `selected` field.
 */
export function isKeywordIncluded(k) {
  return k.selected !== false
}

/** Removes the last extension (e.g. `.png`) for export labels. */
export function stripFileExtension(name) {
  if (name == null) return ''
  const s = String(name).trim()
  if (!s) return ''
  const base = s.replace(/\.[^.]+$/, '')
  return base || s
}

function csvEscape(value) {
  const s = value == null ? '' : String(value)
  // Quote when needed (commas, quotes, newlines). Double any internal quotes.
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

/**
 * Builds a human-readable, batch-level export text for all results.
 * Success entries include only the currently-included keywords.
 */
export function buildCombinedExportText(results) {
  return results
    .map((r) => {
      const raw = r.file?.name ?? ''
      const name = getAccessionNumberFromTitle(raw) || 'unknown'
      if (r.type === 'error') {
        return `${name}\n[Error] ${r.error}`
      }
      const line = r.keywords.filter(isKeywordIncluded).map((k) => k.text).join(', ')
      return `${name}: ${line || '(no keywords selected)'}`
    })
    .join('\n\n')
}

/**
 * CSV export: 2 columns, one keyword per row.
 * - column 1: accession number (derived from title/filename)
 * - column 2: keyword text
 *
 * Errors are skipped (no keyword rows).
 */
export function buildCombinedExportCsv(results) {
  const header = 'accession_number,keyword'
  const rows = results.flatMap((r) => {
    if (r.type !== 'success') return []
    const title = r.file?.name ?? ''
    const accession = getAccessionNumberFromTitle(title) || 'unknown'
    return r.keywords
      .filter(isKeywordIncluded)
      .map((k) => `${csvEscape(accession)},${csvEscape(k.text)}`)
  })

  return [header, ...rows].join('\n')
}

/**
 * Browser download helper for small text exports.
 * Uses an object URL + temporary anchor click.
 */
export function downloadTextFile(filename, text) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
