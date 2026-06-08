import { useNavigate } from 'react-router-dom'
import type { Car } from '../../types/car'
import { resolveCarImageUrl } from '../../utils/images'
import { PLATFORM_LABEL } from './filterOptions'

const fmtKm = (km?: number | null) => {
  if (!km) return '-'
  return km >= 10000 ? `${(km / 10000).toFixed(0)}만km` : `${km.toLocaleString()}km`
}

export default function CarCard({ car }: Props) {
  const navigate = useNavigate()
  const imageUrl = resolveCarImageUrl(car.images?.[0], car.platform)

  return (
    <div className="car-card" onClick={() => navigate(`/cars/${car.id}`)}>
      <div className="car-img-wrap">
        {imageUrl
          ? <img src={imageUrl} alt={car.model ?? ''} loading="lazy" />
          : <div className="car-img-empty"><span>📷</span></div>
        }
        <span className="platform-tag">{PLATFORM_LABEL[car.platform] ?? car.platform}</span>
      </div>

      <div className="car-body">
        <div className="car-title">
          <span className="car-brand">{car.brand}</span>
          <span className="car-model">{car.model}</span>
        </div>
        <div className="car-chips">
          {car.year && <span className="chip">{car.year}년</span>}
          <span className="chip">{fmtKm(car.mileage)}</span>
          {car.fuel && <span className="chip">{car.fuel}</span>}
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
