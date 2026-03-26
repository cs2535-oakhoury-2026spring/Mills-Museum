# Plan: Fix keyword count number input clearing

## Goal
Fix the “number input clears” bug in `UploadScreen.jsx` without reintroducing the clamp behavior issue (where the input is forced to a value while the user is actively deleting/typing).

## Files involved
- `src/frontend/mcam-keyword-generator/src/components/UploadScreen.jsx`
  - Current behavior: both the range slider and the number input are controlled by the same `keywordCount` state, and `onChange` immediately calls `clampKeywordCount(...)`.
  - Bug source: when the number input becomes `''`, the current clamp path converts it into a valid number (so the UI can’t remain empty while editing).
- `src/frontend/mcam-keyword-generator/src/App.jsx`
  - Keep existing backend/front-end clamping on request (`term_count`) as-is. This plan focuses on fixing the *UI editing* behavior.

## Key logic to change (UploadScreen.jsx)
1. Keep the clamp helper for normalization, but stop clamping on every `onChange` keystroke for the *number* input.
2. Introduce a dedicated “number input text” state (string) that can temporarily be `''` while the user clears the field.
3. Only normalize/clamp:
   - when the user clicks “Generate Keywords”
   - and/or on number input `onBlur` (optional; ensures we eventually display a clamped numeric value).

### Suggested implementation outline
- Keep `clampKeywordCount(n)` as the single source of min/max + rounding.
- Add constants (or reuse existing defaults):
  - `DEFAULT_KEYWORD_COUNT = 20`
  - `MIN_KEYWORD_COUNT = 1`
  - `MAX_KEYWORD_COUNT = 50`
- Replace current single state approach:
  - Current: `const [keywordCount, setKeywordCount] = useState(20)`
  - Proposed: 
    - `const [keywordCountText, setKeywordCountText] = useState('20')`
    - (derive numeric only when needed)

### Normalization function (critical to avoid the clearing bug)
Implement a function that explicitly allows `''` during editing:
```js
const normalizeKeywordCountForRequest = (text) => {
  if (text === '') return DEFAULT_KEYWORD_COUNT
  return clampKeywordCount(text)
}
```

## UI behavior rules
- Range input (`type="range"`):
  - On change, set `keywordCountText` to the clamped numeric string (range already stays within bounds).
- Number input (`type="number"`):
  - `value={keywordCountText}`
  - `onChange={(e) => setKeywordCountText(e.target.value)}`
  - Do *not* call `clampKeywordCount` in this handler.
- `handleProcess`:
  - before calling `onRequestProcess(files, ...)`, compute:
    - `const effectiveCount = normalizeKeywordCountForRequest(keywordCountText)`
  - pass `effectiveCount` (number) to the existing `App.jsx` flow.

## Avoiding the “clamp issue reintroduction”
- Do not clamp inside the number input `onChange`.
- The only clamping points should be:
  - range input updates
  - normalize-on-blur (optional)
  - normalize-on-generate (`handleProcess`)

## Verification checklist (manual)
1. Clear the number input with backspace: it should stay visually empty (cursor moves normally) until blur/generate.
2. Type a partial value (e.g. `'' -> 5 -> 50`): the input should not “jump” to 1/20 mid-edit.
3. Click “Generate Keywords” with empty number input: it should generate using `20`.
4. Slider and number field stay in sync after slider interaction.

