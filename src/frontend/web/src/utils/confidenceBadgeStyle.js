/**
 * Confidence color utilities.
 *
 * - `getConfidenceBadgeStyle(confidence)` — small badge inside each tile.
 * - `getHeatmapTileStyle(confidence)` — full-tile background tint.
 *
 * Keeping the color math here prevents duplicated magic numbers and makes
 * visual tweaks easy.
 */
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
  // Linear RGB mix is sufficient here (subtle UI background ramp).
  return {
    r: L(a.r, b.r, t),
    g: L(a.g, b.g, t),
    b: L(a.b, b.b, t),
  }
}

/**
 * Perceived brightness (relative luminance) for sRGB, 0 = black, 1 = white.
 * Coefficients follow WCAG 2.1 so badge text contrast stays predictable.
 */
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
  // Clamp to a stable 0..1 range even if upstream data is missing or malformed.
  const t = Math.max(0, Math.min(100, Number(confidence))) / 100

  const badgeRgb = mixRgb(BADGE_WHITE, BADGE_DARKER, t)
  const badgeBg = rgbStr(badgeRgb)
  const badgeLum = luminance(badgeRgb)
  // Pick a readable foreground across the ramp.
  const badgeFg = badgeLum > 0.72 ? '#334155' : '#0f172a'
  const borderRgb = mixRgb(badgeRgb, parseHex('#64748b'), 0.12 + t * 0.35)
  const badgeBorder = rgbStr(borderRgb)

  return {
    backgroundColor: badgeBg,
    borderColor: badgeBorder,
    color: badgeFg,
  }
}

// ── Heatmap tile background ──
// Low confidence → desaturated / muted blue, high → the normal bright tile blue.
// Scores at or above HEATMAP_CEILING look identical to the default tile color.
// Below that, tiles fade toward a muted gray-blue so low-confidence keywords
// are visually distinct while white text stays readable everywhere.

/** Confidence % at which tiles reach full (normal) color. Adjust as needed. */
const HEATMAP_CEILING = 55

const TILE_LOW = parseHex('#8da0b4')   // muted gray-blue   (0% confidence)
const TILE_HIGH = parseHex('#3b6db5')  // normal tile blue   (HEATMAP_CEILING+)

/**
 * Returns inline styles for a keyword tile background in heatmap mode.
 * `confidence` is 0-100 but the ramp saturates at `HEATMAP_CEILING`.
 * Returns `null` when confidence is missing (still scoring).
 */
export function getHeatmapTileStyle(confidence) {
  if (confidence === null || confidence === undefined) return null

  // Map 0 → HEATMAP_CEILING to 0 → 1, clamp above ceiling to 1
  const t = Math.min(1, Math.max(0, Number(confidence)) / HEATMAP_CEILING)

  const bg = mixRgb(TILE_LOW, TILE_HIGH, t)
  const border = mixRgb(bg, parseHex('#2f5a94'), 0.35)

  return {
    backgroundColor: rgbStr(bg),
    borderColor: rgbStr(border),
  }
}
