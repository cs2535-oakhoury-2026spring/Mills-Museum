import { useState } from 'react'
import NavBar from './NavBar'

export default function ReviewScreen({ results, onUploadNew }) {
    const [index, setIndex] = useState(0)
    const [allResults, setAllResults] = useState(results)

    const current = allResults[index]

    const toggleKeyword = (kwIndex) => {
        setAllResults(prev => {
            const updated = [...prev]
            const kws = [...updated[index].keywords]
            kws[kwIndex] = { ...kws[kwIndex], selected: !kws[kwIndex].selected }
            updated[index] = { ...updated[index], keywords: kws }
            return updated
        })
    }

    const exportText = allResults.map((r, i) => {
        const selected = r.keywords.filter(k => k.selected).map(k => k.label)
        return `Image ${i + 1}: ${selected.join(', ')}`
    }).join('\n\n')

    return (
        <div>
            <div className="image-viewer">
                <img src={current.previewUrl} alt={`artwork ${index + 1}`} />
            </div>

            <NavBar
                current={index}
                total={allResults.length}
                onPrev={() => setIndex(i => Math.max(i - 1, 0))}
                onNext={() => setIndex(i => Math.min(i + 1, allResults.length - 1))}
            />

            <div className="review-columns">
                <div className="keywords-col">
                    <h3>Keywords</h3>
                    <p>Uncheck any keywords you'd like to remove before exporting.</p>
                    <div className="keyword-list">
                        {current.keywords.map((kw, i) => (
                            <label key={i} className="keyword-item">
                                <input
                                    type="checkbox"
                                    checked={kw.selected}
                                    onChange={() => toggleKeyword(i)}
                                />
                                {kw.label} ({kw.score}%)
                            </label>
                        ))}
                    </div>
                </div>

                <div className="export-col">
                    <h3>Exported Keywords</h3>
                    <textarea readOnly value={exportText} />
                </div>
            </div>

            <div className="action-row">
                <button className="btn-primary" disabled>
                    Export Selected Keywords
                </button>
                <button className="btn-secondary" onClick={onUploadNew}>
                    Upload New Images
                </button>
            </div>
        </div>
    )
}