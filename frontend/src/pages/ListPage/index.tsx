import CarCard from './CarCard'
import FilterPanel from './FilterPanel'
import { useCarCategories } from './useCarCategories'
import { useCarList } from './useCarList'

export default function ListPage() {
  const { data: filterOptions } = useCarCategories()
  const { data, isLoading, isFetching, filters, setFilter, setFilterValues, setPage, resetFilters } = useCarList()

  const currentPage = filters.page ?? 1
  const hasMore = data?.has_next ?? false
  const title = [filters.brand, filters.model_group].filter(Boolean).join(' ') || '전체 매물'

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">{title}</h1>
        {data && <p className="page-sub">{data.items.length}개 매물 · {currentPage} 페이지</p>}
      </div>

      <FilterPanel
        options={filterOptions}
        filters={filters}
        setFilter={setFilter}
        setFilterValues={setFilterValues}
        resetFilters={resetFilters}
      />

      {(isLoading || isFetching) && <div className="loading-bar" />}

      {!isLoading && data?.items.length === 0 && (
        <p className="status">검색 결과가 없어요. 필터를 조정해보세요.</p>
      )}

      <div className="car-grid">
        {data?.items.map(car => <CarCard key={car.id} car={car} />)}
      </div>

      {data && data.items.length > 0 && (
        <div className="pagination">
          <button disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>이전</button>
          <span>{currentPage} 페이지</span>
          <button disabled={!hasMore} onClick={() => setPage(currentPage + 1)}>다음</button>
        </div>
      )}
    </div>
  )
}
