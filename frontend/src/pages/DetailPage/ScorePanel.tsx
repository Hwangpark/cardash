import type { Score } from '../../types/car'

const GRADE_META: Record<string, { color: string; bg: string; label: string }> = {
  'S':  { color: '#92400e', bg: '#fef3c7', label: '최상급' },
  'A+': { color: '#065f46', bg: '#d1fae5', label: '매우 우수' },
  'A':  { color: '#1e40af', bg: '#dbeafe', label: '우수' },
  'B':  { color: '#1e3a8a', bg: '#e0e7ff', label: '양호' },
  'C':  { color: '#92400e', bg: '#fef3c7', label: '보통' },
  'D':  { color: '#9a3412', bg: '#ffedd5', label: '미흡' },
  'F':  { color: '#991b1b', bg: '#fee2e2', label: '불량' },
}

const GRADE_BAR: Record<string, string> = {
  'S': '#f59e0b', 'A+': '#10b981', 'A': '#3b82f6',
  'B': '#6366f1', 'C':  '#f59e0b', 'D': '#f97316', 'F': '#ef4444',
}

const ITEMS = [
  { key: 'accident',     label: '사고/보험', icon: '🛡️', max: 25 },
  { key: 'inspection',   label: '성능점검',  icon: '🔧', max: 20 },
  { key: 'mileage',      label: '주행거리',  icon: '📍', max: 15 },
  { key: 'price',        label: '가격 적정', icon: '💰', max: 15 },
  { key: 'rental',       label: '렌트이력',  icon: '🚕', max: 15 },
  { key: 'owner_changes', label: '소유주변경', icon: '👤', max: 10 },
] as const

export default function ScorePanel({ score, sourceUrl }: { score: Score; sourceUrl?: string | null }) {
  const meta  = GRADE_META[score.grade]  ?? GRADE_META['C']
  const color = GRADE_BAR[score.grade] ?? '#6366f1'

  return (
    <div className="score-panel">
      {/* 헤더: 등급 + 점수 */}
      <div className="score-summary">
        <div className="grade-pill" style={{ background: meta.bg, color: meta.color }}>
          <span className="grade-letter">{score.grade}</span>
          <span className="grade-label">{meta.label}</span>
        </div>
        <div className="score-num">
          <span className="score-big">{score.total}</span>
          <span className="score-denom">/100점</span>
        </div>
      </div>

      {/* 경고 */}
      {score.penalty > 0 && (
        <div className="score-alert">⚠️ 비공개 이력으로 {score.penalty}점 감점 적용</div>
      )}
      {score.insurance_fetch_status === 'viewable_unfetched' && (
        <div className="score-alert info">
          ℹ️ 보험이력 조회 가능 — 자동 수집에 실패해 추정치(40%)가 적용됐어요.{' '}
          {sourceUrl && <a href={sourceUrl} target="_blank" rel="noreferrer">원본에서 직접 확인</a>}
        </div>
      )}
      {score.insurance_fetch_status === 'reregistered_listing' && (
        <div className="score-alert info">
          ℹ️ 보험이력 조회 불가 — 재등록/매물갱신으로 추정되어 원본에서도 이력 확인이 어려울 수 있어요. (추정치 40% 적용)
        </div>
      )}
      {(score.insurance_fetch_status === 'unavailable' || score.insurance_fetch_status === 'not_applicable') && (
        <div className="score-alert info">ℹ️ 보험이력 미제공 차량 — 최대 A등급으로 제한</div>
      )}

      {/* 항목별 바 */}
      <div className="score-rows">
        {ITEMS.map(({ key, label, icon, max }) => {
          const val = score[key] as number
          const pct = Math.round((val / max) * 100)
          return (
            <div key={key} className="score-item">
              <div className="score-item-header">
                <span className="score-item-label">{icon} {label}</span>
                <span className="score-item-val" style={{ color }}>{val.toFixed(1)}<em>/{max}</em></span>
              </div>
              <div className="score-bar-track">
                <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
