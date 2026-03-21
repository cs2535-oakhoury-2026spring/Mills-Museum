export function mapApiKeyword(kw) {
  const raw = kw.score
  const score = typeof raw === 'number' ? raw : parseFloat(raw)
  return {
    text: kw.label ?? kw.text ?? '',
    confidence: Number.isFinite(score) ? Math.round(score * 10) / 10 : 0,
    selected: true,
  }
}

/** Keyword is included in exports when `selected` is not explicitly false. */
export function isKeywordIncluded(k) {
  return k.selected !== false
}

export function buildCombinedExportText(results) {
  return results
    .map((r, i) => {
      if (r.type === 'error') {
        return `Image ${i + 1}: ${r.file.name}\n[Error] ${r.error}`
      }
      const line = r.keywords.filter(isKeywordIncluded).map((k) => k.text).join(', ')
      return `Image ${i + 1}: ${line || '(no keywords selected)'}`
    })
    .join('\n\n')
}

export function downloadTextFile(filename, text) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
