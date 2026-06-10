import { useNavigate } from 'react-router-dom'
import type { Car } from '../../types/car'
import { resolveCarImageUrl } from '../../utils/images'
import { PLATFORM_LABEL } from './filterOptions'

// 등급별 색상 — CarGurus 연구: 색상 코딩이 텍스트보다 신뢰 신호 처리 속도 3배 빠름
const GRADE_BG: Record<string, string> = {
  'S':  '#f59e0b',
  'A+': '#10b981',
  'A':  '#3b82f6',
  'B':  '#6366f1',
  'C':  '#ca8a04',
  'D':  '#ea580c',
  'F':  '#dc2626',
}

const fmtKm = (km?: number | null) => {
  if (!km) return '-'
  if (km < 10000) return `${km.toLocaleString()}km`
  return `${parseFloat((km / 10000).toFixed(1))}만km`
}

const fmtSeller = (t: string | null) => {
  if (t === 'dealer')  return '딜러'
  if (t === 'private' || t === 'individual') return '개인'
  return null
}

export default function CarCard({ car }: Props) {
  const navigate = useNavigate()
  const imageUrl = resolveCarImageUrl(car.images?.[0], car.platform)
  const score = car.score_summary

  return (
    <div className="car-card" onClick={() => navigate(`/cars/${car.id}`)}>
      <div className="car-img-wrap">
        {imageUrl
          ? <img src={imageUrl} alt={car.model ?? ''} loading="lazy" />
          : <div className="car-img-empty"><span>📷</span></div>
        }
        <span className="platform-tag">{PLATFORM_LABEL[car.platform] ?? car.platform}</span>
        {score && (
          <span className="car-grade-badge" style={{ background: GRADE_BG[score.grade] }}>
            {score.grade}
          </span>
        )}
      </div>

      <div className="car-body">
        <div className="car-title">
          <span className="car-brand">{car.brand}</span>
          <span className="car-model">{car.model}</span>
        </div>

        <div className="car-chips">
          {car.year && <span className="chip">{car.year}년</span>}
          <span className="chip chip--km">{fmtKm(car.mileage)}</span>
          {car.fuel && <span className="chip">{car.fuel}</span>}
          {car.transmission && <span className="chip">{car.transmission}</span>}
        </div>

        <div className="car-trust-row">
          {score?.accident_free === true && (
            <span className="chip-trust chip-trust--safe">🛡️ 무사고</span>
          )}
          {score?.accident_free === false && (
            <span className="chip-trust chip-trust--warn">사고이력</span>
          )}
          {score?.owner_change_count != null && (
            <span className={`chip-trust ${score.owner_change_count === 0 ? 'chip-trust--safe' : score.owner_change_count >= 2 ? 'chip-trust--warn' : 'chip-trust--neutral'}`}>
              {score.owner_change_count === 0 ? '1인 소유' : `${score.owner_change_count}회 변경`}
            </span>
          )}
          {fmtSeller(car.seller_type) && (
            <span className="chip-trust chip-trust--neutral">{fmtSeller(car.seller_type)}</span>
          )}
        </div>

        <div className="car-footer">
          <span className="car-price">{car.price?.toLocaleString()}만원</span>
          {car.region && <span className="car-loc">📍{car.region}</span>}
        </div>
      </div>
    </div>
  )
}

interface Props { car: Car }
