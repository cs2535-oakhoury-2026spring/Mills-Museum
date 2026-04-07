const L = (a, b, t) => a + (b - a) * t

function parseHex(hex) {
  const h = hex.replace('#', '')
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  }
}

function rgbStr(rgb) {
  return `rgb(${Math.round(rgb.r)}, ${Math.round(rgb.g)}, ${Math.round(rgb.b)})`
}

function mixRgb(a, b, t) {
  return {
    r: L(a.r, b.r, t),
    g: L(a.g, b.g, t),
    b: L(a.b, b.b, t),
  }
}

function luminance(rgb) {
  return (0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b) / 255
}

/** White at low confidence → cooler, darker off-white / blue-gray at high confidence */
const BADGE_WHITE = parseHex('#ffffff')
const BADGE_DARKER = parseHex('#b8c9dc')

/**
 * Confidence % in a white box that darkens as confidence rises (stays on-brand, cool tones).
 */
export function getConfidenceBadgeStyle(confidence) {
  const t = Math.max(0, Math.min(100, Number(confidence))) / 100

  const badgeRgb = mixRgb(BADGE_WHITE, BADGE_DARKER, t)
  const badgeBg = rgbStr(badgeRgb)
  const badgeLum = luminance(badgeRgb)
  const badgeFg = badgeLum > 0.72 ? '#334155' : '#0f172a'
  const borderRgb = mixRgb(badgeRgb, parseHex('#64748b'), 0.12 + t * 0.35)
  const badgeBorder = rgbStr(borderRgb)

  return {
    backgroundColor: badgeBg,
    borderColor: badgeBorder,
    color: badgeFg,
  }
}
