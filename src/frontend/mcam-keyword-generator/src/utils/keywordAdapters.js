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

/** Keyword is included in exports when `selected` is not explicitly false. */
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

export function buildCombinedExportText(results) {
  return results
    .map((r) => {
      const raw = r.file?.name
      const name =
        raw != null && raw !== '' ? stripFileExtension(raw) : 'unknown'
      if (r.type === 'error') {
        return `${name}\n[Error] ${r.error}`
      }
      const line = r.keywords.filter(isKeywordIncluded).map((k) => k.text).join(', ')
      return `${name}: ${line || '(no keywords selected)'}`
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
