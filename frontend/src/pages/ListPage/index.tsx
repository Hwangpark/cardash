import CarCard from './CarCard'
import { useCarList } from './useCarList'

const BRANDS = ['현대', '기아', '쉐보레(GM대우)', '르노코리아(삼성)', 'BMW', '벤츠', '아우디', '볼보']
const REGIONS = ['서울', '경기', '인천', '부산', '대구', '광주', '대전']

export default function ListPage() {
  const { data, isLoading, filters, setFilter, setPage } = useCarList()

  return (
    <div className="page">
      <h1 className="page-title">중고차 통합 대시보드</h1>

      <div className="filter-bar">
        <select onChange={e => setFilter('brand', e.target.value)} value={filters.brand ?? ''}>
          <option value="">브랜드 전체</option>
          {BRANDS.map(b => <option key={b} value={b}>{b}</option>)}
        </select>
        <input
          type="number" placeholder="최저가 (만원)"
          onChange={e => setFilter('price_min', Number(e.target.value))}
        />
        <input
          type="number" placeholder="최고가 (만원)"
          onChange={e => setFilter('price_max', Number(e.target.value))}
        />
        <input
          type="number" placeholder="최대 주행거리 (km)"
          onChange={e => setFilter('mileage_max', Number(e.target.value))}
        />
        <select onChange={e => setFilter('region', e.target.value)} value={filters.region ?? ''}>
          <option value="">지역 전체</option>
          {REGIONS.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {isLoading && <p className="status">불러오는 중...</p>}

      <div className="car-grid">
        {data?.items.map(car => <CarCard key={car.id} car={car} />)}
      </div>

      {data && (
        <div className="pagination">
          <button disabled={filters.page === 1} onClick={() => setPage((filters.page ?? 1) - 1)}>이전</button>
          <span>{filters.page ?? 1} 페이지</span>
          <button disabled={(data.items.length ?? 0) < (filters.size ?? 20)} onClick={() => setPage((filters.page ?? 1) + 1)}>다음</button>
        </div>
      )}
    </div>
  )
}
