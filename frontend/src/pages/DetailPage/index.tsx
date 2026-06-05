import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { analyzeCarDetail, fetchCarDetail } from '../../api/cars'
import { resolveCarImageUrl } from '../../utils/images'
import ScorePanel from './ScorePanel'

export default function DetailPage() {
  const { id } = useParams<{ id: string }>()
  const carId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['car', carId],
    queryFn: () => fetchCarDetail(carId),
  })

  const analyze = useMutation({
    mutationFn: () => analyzeCarDetail(carId),
    onSuccess: (result) => {
      queryClient.setQueryData(['car', carId], result)
    },
  })

  if (isLoading) return <div className="page"><p className="status">불러오는 중...</p></div>
  if (!data?.car) return <div className="page"><p className="status">차량을 찾을 수 없습니다.</p></div>

  const { car, score } = data
  const imageUrl = resolveCarImageUrl(car.images?.[0], car.platform)

  return (
    <div className="page">
      <button className="back-btn" onClick={() => navigate(-1)}>← 목록으로</button>

      <div className="detail-layout">
        <div className="detail-left">
          {imageUrl && <img className="detail-image" src={imageUrl} alt={car.model ?? ''} />}
          <div className="detail-info">
            <h2>{car.brand} {car.model}</h2>
            <p>{car.year}년 · {car.mileage?.toLocaleString()}km · {car.fuel} · {car.transmission}</p>
            <p>색상: {car.color} · 지역: {car.region}</p>
            <p className="detail-price">{car.price?.toLocaleString()}만원</p>
            {car.url && <a href={car.url} target="_blank" rel="noreferrer" className="source-link">원본 매물 보기 →</a>}
          </div>
        </div>

        <div className="detail-right">
          {score
            ? <ScorePanel score={score} />
            : (
              <div className="analyze-box">
                <p>아직 분석되지 않은 매물이에요.</p>
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
    </div>
  )
}
