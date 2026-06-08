import type { CarFilterOptions, CarFilterValue, CarFilters } from '../../types/car'
import {
  FALLBACK_MAKES, MILEAGE_OPTIONS, PLATFORM_OPTIONS,
  PRICE_OPTIONS, REGION_OPTIONS, YEAR_OPTIONS,
} from './filterOptions'

interface Props {
  options?: CarFilterOptions
  filters: CarFilters
  setFilter: (key: keyof CarFilters, value: CarFilterValue) => void
  setFilterValues: (patch: Partial<CarFilters>) => void
  resetFilters: () => void
}

type LabelValue = { label: string; value: string | number }

function Select({ label, value, items, disabled, onChange }: {
  label: string; value?: string | number; items: LabelValue[]
  disabled?: boolean; onChange: (v: string | undefined) => void
}) {
  return (
    <div className="filter-group">
      <label className="filter-label">{label}</label>
      <select
        disabled={disabled}
        value={value !== undefined ? String(value) : ''}
        onChange={e => onChange(e.target.value || undefined)}
      >
        <option value="">전체</option>
        {items.map(o => <option key={o.value} value={String(o.value)}>{o.label}</option>)}
      </select>
    </div>
  )
}

const hasActiveFilter = (f: CarFilters) =>
  !!(f.platform || f.brand || f.model_group || f.year_min || f.year_max ||
     f.price_min || f.price_max || f.mileage_max || f.region)

export default function FilterPanel({ options, filters, setFilter, setFilterValues, resetFilters }: Props) {
  const brands = options?.brands ?? FALLBACK_MAKES
  const modelGroups = filters.brand ? (options?.model_groups[filters.brand] ?? []) : []

  const onBrandChange = (brand: string | undefined) =>
    setFilterValues({ brand, model_group: undefined })

  const onModelGroupChange = (mg: string | undefined) =>
    setFilterValues({ model_group: mg })

  return (
    <div className="filter-panel">
      <div className="filter-row">
        {/* 플랫폼 */}
        <Select label="플랫폼" value={filters.platform}
          items={PLATFORM_OPTIONS.map(o => ({ label: o.label, value: o.value }))}
          onChange={v => setFilter('platform', v)} />

        {/* 제조사 */}
        <Select label="제조사" value={filters.brand}
          items={brands.map(b => ({ label: b, value: b }))}
          onChange={onBrandChange} />

        {/* 모델 그룹 */}
        <Select label="모델" value={filters.model_group}
          items={modelGroups.map(g => ({ label: g, value: g }))}
          disabled={!filters.brand || modelGroups.length === 0}
          onChange={onModelGroupChange} />

        {/* 연식 */}
        <Select label="연식 (최소)" value={filters.year_min}
          items={YEAR_OPTIONS.map(y => ({ label: `${y}년`, value: y }))}
          onChange={v => setFilter('year_min', v ? Number(v) : undefined)} />
        <Select label="연식 (최대)" value={filters.year_max}
          items={YEAR_OPTIONS.map(y => ({ label: `${y}년`, value: y }))}
          onChange={v => setFilter('year_max', v ? Number(v) : undefined)} />

        {/* 가격 */}
        <Select label="가격 (최대)" value={filters.price_max}
          items={PRICE_OPTIONS.map(o => ({ label: o.label, value: o.value }))}
          onChange={v => setFilter('price_max', v ? Number(v) : undefined)} />

        {/* 주행거리 */}
        <Select label="주행거리 (최대)" value={filters.mileage_max}
          items={MILEAGE_OPTIONS.map(o => ({ label: o.label, value: o.value }))}
          onChange={v => setFilter('mileage_max', v ? Number(v) : undefined)} />

        {/* 지역 */}
        <Select label="지역" value={filters.region}
          items={REGION_OPTIONS.map(r => ({ label: r, value: r }))}
          onChange={v => setFilter('region', v)} />
      </div>

      {hasActiveFilter(filters) && (
        <div className="filter-active-bar">
          {filters.platform && <span className="filter-chip">{filters.platform} ×<button onClick={() => setFilter('platform', undefined)} /></span>}
          {filters.brand && <span className="filter-chip">{filters.brand} ×<button onClick={() => onBrandChange(undefined)} /></span>}
          {filters.model_group && <span className="filter-chip">{filters.model_group} ×<button onClick={() => onModelGroupChange(undefined)} /></span>}
          {filters.year_min && <span className="filter-chip">{filters.year_min}년~ ×<button onClick={() => setFilter('year_min', undefined)} /></span>}
          {filters.year_max && <span className="filter-chip">~{filters.year_max}년 ×<button onClick={() => setFilter('year_max', undefined)} /></span>}
          {filters.price_max && <span className="filter-chip">{filters.price_max?.toLocaleString()}만원 이하 ×<button onClick={() => setFilter('price_max', undefined)} /></span>}
          {filters.mileage_max && <span className="filter-chip">{(filters.mileage_max / 10000).toFixed(0)}만km 이하 ×<button onClick={() => setFilter('mileage_max', undefined)} /></span>}
          {filters.region && <span className="filter-chip">{filters.region} ×<button onClick={() => setFilter('region', undefined)} /></span>}
          <button className="filter-reset" onClick={resetFilters}>전체 초기화</button>
        </div>
      )}
    </div>
  )
}
