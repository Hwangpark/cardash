import type { Score } from '../../types/car'

const GRADE_COLOR: Record<string, string> = {
  S: '#FFD700', 'A+': '#00C851', A: '#33b5e5',
  B: '#2BBBAD', C: '#ffbb33', D: '#ff8800', F: '#ff4444',
}

const ITEMS = [
  { key: 'accident', label: '사고/보험', max: 25 },
  { key: 'inspection', label: '성능점검', max: 20 },
  { key: 'mileage', label: '주행거리', max: 15 },
  { key: 'price', label: '가격', max: 15 },
  { key: 'rental', label: '렌트이력', max: 15 },
  { key: 'owner_changes', label: '소유주변경', max: 10 },
] as const

interface Props {
  score: Score
}

export default function ScorePanel({ score }: Props) {
  const color = GRADE_COLOR[score.grade] ?? '#888'

  return (
    <div className="score-panel">
      <div className="score-header">
        <div className="grade-badge" style={{ background: color }}>{score.grade}</div>
        <div className="score-total">{score.total}점</div>
      </div>
      {score.penalty > 0 && (
        <p className="penalty-note">⚠ 비공개 이력으로 {score.penalty}점 감점</p>
      )}
      {score.no_insurance_data && (
        <p className="penalty-note">ℹ 보험이력 미제공 — 최대 A등급</p>
      )}
      <div className="score-items">
        {ITEMS.map(({ key, label, max }) => {
          const val = score[key] as number
          return (
            <div key={key} className="score-row">
              <span className="score-label">{label}</span>
              <div className="score-bar-bg">
                <div className="score-bar-fill" style={{ width: `${(val / max) * 100}%`, background: color }} />
              </div>
              <span className="score-value">{val.toFixed(1)} / {max}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
