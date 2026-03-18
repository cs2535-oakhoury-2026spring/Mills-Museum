export default function NavBar({ current, total, onPrev, onNext }) {
  return (
    <div className="nav-bar">
      <button onClick={onPrev} disabled={current <= 0}>←</button>
      <span className="counter">
        {total === 0 ? '—' : `${current + 1} of ${total}`}
      </span>
      <button onClick={onNext} disabled={current >= total - 1}>→</button>
    </div>
  )
}