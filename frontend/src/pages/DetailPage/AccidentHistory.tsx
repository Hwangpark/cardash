import type { AccidentRecord } from '../../types/car'

function formatWon(amount: number) {
  return amount > 0 ? `${amount.toLocaleString()}원` : '-'
}

export default function AccidentHistory({ records, hasInsuranceData }: {
  records: AccidentRecord[] | null
  hasInsuranceData: boolean
}) {
  if (!hasInsuranceData) return null

  return (
    <div className="accident-history">
      <h3 className="accident-history-title">🛡️ 보험사고 이력</h3>
      {!records || records.length === 0
        ? <p className="accident-history-empty">보험 처리된 사고 이력이 없어요.</p>
        : (
          <ul className="accident-history-list">
            {records.map((r, i) => (
              <li key={i} className="accident-history-item">
                <div className="accident-history-row">
                  <span className="accident-history-date">{r.date ?? '날짜 미상'}</span>
                  <span className="accident-history-benefit">보험금 {formatWon(r.insurance_benefit)}</span>
                </div>
                {(r.part_cost > 0 || r.labor_cost > 0 || r.painting_cost > 0) && (
                  <div className="accident-history-breakdown">
                    부품비 {formatWon(r.part_cost)} · 공임 {formatWon(r.labor_cost)} · 도장비 {formatWon(r.painting_cost)}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )
      }
    </div>
  )
}
