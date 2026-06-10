import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { analyzeCarDetail, fetchCarDetail } from '../../api/cars'
import { resolveCarImageUrl } from '../../utils/images'
import { getPlatformLabel } from '../ListPage/filterOptions'
import AccidentHistory from './AccidentHistory'
import ScorePanel from './ScorePanel'

export default function DetailPage() {
  const { id } = useParams<{ id: string }>()
  const carId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeImg, setActiveImg] = useState(0)

  const { data, isLoading } = useQuery({
    queryKey: ['car', carId],
    queryFn: () => fetchCarDetail(carId),
  })

  const analyze = useMutation({
    mutationFn: () => analyzeCarDetail(carId),
    onSuccess: result => queryClient.setQueryData(['car', carId], result),
  })

  if (isLoading) return <div className="page"><p className="status">불러오는 중...</p></div>
  if (!data?.car) return <div className="page"><p className="status">차량을 찾을 수 없습니다.</p></div>

  const { car, score } = data
  const images = (car.images ?? [])
    .map(img => resolveCarImageUrl(img, car.platform))
    .filter(Boolean) as string[]

  return (
    <div className="page">
      <button className="back-btn" onClick={() => navigate(-1)}>← 목록으로</button>

      <div className="detail-top">
        {/* 이미지 갤러리 */}
        <div className="gallery">
          <div className="gallery-main">
            {images.length > 0
              ? <img src={images[activeImg]} alt={car.model ?? ''} />
              : <div className="gallery-empty">이미지 없음</div>
            }
            <span className="gallery-platform">{getPlatformLabel(car.platform)}</span>
          </div>
          {images.length > 1 && (
            <div className="gallery-thumbs">
              {images.map((src, i) => (
                <img key={i} src={src} alt="" className={i === activeImg ? 'active' : ''}
                  onClick={() => setActiveImg(i)} />
              ))}
            </div>
          )}
        </div>

        {/* 차량 기본 정보 */}
        <div className="detail-info">
          <div className="detail-header">
            <h2>{car.brand} {car.model}</h2>
            {car.trim && <p className="detail-trim">{car.trim}</p>}
            <p className="detail-price">{car.price?.toLocaleString()}만원</p>
          </div>

          <div className="spec-grid">
            <SpecItem label="연식"    value={car.year ? `${car.year}년` : '-'} />
            <SpecItem label="주행거리" value={car.mileage ? `${car.mileage.toLocaleString()}km` : '-'} />
            <SpecItem label="연료"    value={car.fuel ?? '-'} />
            <SpecItem label="변속기"  value={car.transmission ?? '-'} />
            <SpecItem label="색상"    value={car.color ?? '-'} />
            <SpecItem label="지역"    value={car.region ?? '-'} />
            <SpecItem label="판매자"  value={car.seller_type === 'dealer' ? '딜러' : '개인'} />
            <SpecItem label="플랫폼"  value={getPlatformLabel(car.platform)} />
          </div>

          {car.url && (
            <a href={car.url} target="_blank" rel="noreferrer" className="source-link">
              원본 매물 보기 →
            </a>
          )}
        </div>
      </div>

      {/* 점수 패널 */}
      <div className="detail-score-section">
        {score
          ? (
            <>
              <ScorePanel score={score} sourceUrl={car.url} />
              <AccidentHistory records={score.accident_history} hasInsuranceData={!score.no_insurance_data} />
            </>
          )
          : (
            <div className="analyze-box">
              <div className="analyze-icon">🔍</div>
              <p>사고이력, 성능점검, 가격 적정성 등을<br />종합 분석해드릴게요.</p>
              <button
                className="analyze-btn"
                onClick={() => analyze.mutate()}
                disabled={analyze.isPending}
              >
                {analyze.isPending ? '분석 중...' : '지금 분석하기'}
              </button>
              {analyze.isError && <p className="error-note">분석 중 오류가 발생했어요. 다시 시도해주세요.</p>}
            </div>
          )
        }
      </div>
    </div>
  )
}

function SpecItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="spec-item">
      <span className="spec-label">{label}</span>
      <span className="spec-value">{value}</span>
    </div>
  )
}
