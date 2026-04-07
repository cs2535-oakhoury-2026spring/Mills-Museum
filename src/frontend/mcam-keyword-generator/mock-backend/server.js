const express = require('express')
const cors = require('cors')
const multer = require('multer')

const app = express()
const upload = multer({ storage: multer.memoryStorage() })

// Allow the Vite dev server to call the mock endpoint during local testing.
app.use(
  cors({
    origin: [
      'http://localhost:5173',
      'http://127.0.0.1:5173',
      'http://localhost:3001',
      'http://127.0.0.1:3001',
      '*',
    ],
  }),
)

// Fixed list to keep the UI stable while you design.
const FIXED_KEYWORDS = [
  { label: 'Still life', score: 92.4 },
  { label: 'Ceramics', score: 87.1 },
  { label: 'Interior', score: 84.3 },
  { label: 'Tabletop objects', score: 80.2 },
  { label: 'Vase', score: 78.6 },
  { label: 'Fruit', score: 76.9 },
  { label: 'Museum cataloging', score: 74.8 },
  { label: 'Domestic scene', score: 71.5 },
  { label: 'Artistic style', score: 69.2 },
  { label: 'Decorative arts', score: 66.7 },
]

app.post('/predict', upload.single('file'), async (req, res) => {
  // The UI expects: { keywords: [{ label, score }, ...] }
  // This mock ignores the uploaded file and always returns the same list.
  res.json({ keywords: FIXED_KEYWORDS })
})

const port = process.env.PORT || 8000
app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Mock /predict backend listening on http://localhost:${port}`)
})

