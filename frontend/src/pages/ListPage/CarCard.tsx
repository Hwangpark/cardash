import { useNavigate } from 'react-router-dom'
import type { Car } from '../../types/car'
import { resolveCarImageUrl } from '../../utils/images'
import { PLATFORM_LABEL } from './filterOptions'

interface Props {
  car: Car
}

export default function CarCard({ car }: Props) {
  const navigate = useNavigate()
  const imageUrl = resolveCarImageUrl(car.images?.[0], car.platform)

  return (
    <div className="car-card" onClick={() => navigate(`/cars/${car.id}`)}>
      <div className="car-card-image">
        {imageUrl
          ? <img src={imageUrl} alt={car.model ?? ''} />
          : <div className="car-card-no-image">이미지 없음</div>
        }
        <span className="platform-badge">{PLATFORM_LABEL[car.platform] ?? car.platform}</span>
      </div>
      <div className="car-card-body">
        <p className="car-name">{car.brand} {car.model}</p>
        <p className="car-sub">{car.year}년 · {car.mileage?.toLocaleString()}km · {car.fuel}</p>
        <p className="car-price">{car.price?.toLocaleString()}만원</p>
        <p className="car-region">{car.region}</p>
      </div>
    </div>
  )
}
