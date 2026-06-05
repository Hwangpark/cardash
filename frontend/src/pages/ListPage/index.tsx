import CarCard from './CarCard'
import FilterPanel from './FilterPanel'
import { useCarCategories } from './useCarCategories'
import { useCarList } from './useCarList'

export default function ListPage() {
  const { data: filterOptions } = useCarCategories()
  const { data, isLoading, filters, setFilter, setFilterValues, setPage } = useCarList()

  const currentPage = filters.page ?? 1
  const hasMore = (data?.items.length ?? 0) >= (filters.size ?? 20)

  return (
    <div className="page">
      <h1 className="page-title">중고차 통합 대시보드</h1>

      <FilterPanel
        options={filterOptions}
        filters={filters}
        setFilter={setFilter}
        setFilterValues={setFilterValues}
      />

      {isLoading && <p className="status">불러오는 중...</p>}

      <div className="car-grid">
        {data?.items.map(car => <CarCard key={car.id} car={car} />)}
      </div>

      {!isLoading && data?.items.length === 0 && (
        <p className="status">검색 결과가 없습니다.</p>
      )}

      {data && (
        <div className="pagination">
          <button disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>이전</button>
          <span>{currentPage} 페이지</span>
          <button disabled={!hasMore} onClick={() => setPage(currentPage + 1)}>다음</button>
        </div>
      )}
    </div>
  )
}
