import type { CarFilterOptions, CarFilterValue, CarFilters } from '../../types/car'
import {
  FALLBACK_MAKES, GRADE_OPTIONS, MILEAGE_OPTIONS, PLATFORM_LABEL, PLATFORM_OPTIONS,
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

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="filter-chip">
      {label}
      <button onClick={onRemove}>×</button>
    </span>
  )
}

const OWNER_CHANGE_OPTIONS: LabelValue[] = [
  { label: '1회 이하', value: 1 },
  { label: '2회 이하', value: 2 },
  { label: '3회 이하', value: 3 },
]

const hasActiveFilter = (f: CarFilters) =>
  !!(f.platform || f.brand || f.model_group || f.year_min || f.year_max ||
     f.price_min || f.price_max || f.mileage_max || f.region || f.grade_min ||
     f.accident_free || f.owner_changes_max || f.has_insurance_data)

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
        <Select label="플랫폼" value={filters.platform}
          items={PLATFORM_OPTIONS.map(o => ({ label: o.label, value: o.value }))}
          onChange={v => setFilter('platform', v)} />

        <Select label="제조사" value={filters.brand}
          items={brands.map(b => ({ label: b, value: b }))}
          onChange={onBrandChange} />

        <Select label="모델" value={filters.model_group}
          items={modelGroups.map(g => ({ label: g, value: g }))}
          disabled={!filters.brand || modelGroups.length === 0}
          onChange={onModelGroupChange} />

        <Select label="연식 (최소)" value={filters.year_min}
          items={YEAR_OPTIONS.map(y => ({ label: `${y}년`, value: y }))}
          onChange={v => setFilter('year_min', v ? Number(v) : undefined)} />
        <Select label="연식 (최대)" value={filters.year_max}
          items={YEAR_OPTIONS.map(y => ({ label: `${y}년`, value: y }))}
          onChange={v => setFilter('year_max', v ? Number(v) : undefined)} />

        <Select label="가격 (최대)" value={filters.price_max}
          items={PRICE_OPTIONS.map(o => ({ label: o.label, value: o.value }))}
          onChange={v => setFilter('price_max', v ? Number(v) : undefined)} />

        <Select label="주행거리 (최대)" value={filters.mileage_max}
          items={MILEAGE_OPTIONS.map(o => ({ label: o.label, value: o.value }))}
          onChange={v => setFilter('mileage_max', v ? Number(v) : undefined)} />

        <Select label="지역" value={filters.region}
          items={REGION_OPTIONS.map(r => ({ label: r, value: r }))}
          onChange={v => setFilter('region', v)} />

        <Select label="등급" value={filters.grade_min}
          items={GRADE_OPTIONS}
          onChange={v => setFilter('grade_min', v)} />

        <Select label="소유주 변경 (최대)" value={filters.owner_changes_max}
          items={OWNER_CHANGE_OPTIONS}
          onChange={v => setFilter('owner_changes_max', v ? Number(v) : undefined)} />

        <label className="filter-group filter-checkbox">
          <span className="filter-label">사고 이력</span>
          <span className="filter-checkbox-row">
            <input
              type="checkbox"
              checked={filters.accident_free === '1'}
              onChange={e => setFilter('accident_free', e.target.checked ? '1' : undefined)}
            />
            무사고만 보기
          </span>
        </label>

        <label className="filter-group filter-checkbox">
          <span className="filter-label">보험이력 조회</span>
          <span className="filter-checkbox-row">
            <input
              type="checkbox"
              checked={filters.has_insurance_data === '1'}
              onChange={e => setFilter('has_insurance_data', e.target.checked ? '1' : undefined)}
            />
            조회 불가 차량 제외
          </span>
        </label>
      </div>

      {hasActiveFilter(filters) && (
        <div className="filter-active-bar">
          {filters.platform && <Chip label={PLATFORM_LABEL[filters.platform] ?? filters.platform} onRemove={() => setFilter('platform', undefined)} />}
          {filters.brand && <Chip label={filters.brand} onRemove={() => onBrandChange(undefined)} />}
          {filters.model_group && <Chip label={filters.model_group} onRemove={() => onModelGroupChange(undefined)} />}
          {filters.year_min && <Chip label={`${filters.year_min}년~`} onRemove={() => setFilter('year_min', undefined)} />}
          {filters.year_max && <Chip label={`~${filters.year_max}년`} onRemove={() => setFilter('year_max', undefined)} />}
          {filters.price_max && <Chip label={`${filters.price_max?.toLocaleString()}만원 이하`} onRemove={() => setFilter('price_max', undefined)} />}
          {filters.mileage_max && <Chip label={`${(filters.mileage_max / 10000).toFixed(0)}만km 이하`} onRemove={() => setFilter('mileage_max', undefined)} />}
          {filters.region && <Chip label={filters.region} onRemove={() => setFilter('region', undefined)} />}
          {filters.grade_min && <Chip label={`${filters.grade_min} 이상`} onRemove={() => setFilter('grade_min', undefined)} />}
          {filters.owner_changes_max && <Chip label={`소유주 변경 ${filters.owner_changes_max}회 이하`} onRemove={() => setFilter('owner_changes_max', undefined)} />}
          {filters.accident_free === '1' && <Chip label="무사고" onRemove={() => setFilter('accident_free', undefined)} />}
          {filters.has_insurance_data === '1' && <Chip label="보험이력 조회 불가 제외" onRemove={() => setFilter('has_insurance_data', undefined)} />}
          <button className="filter-reset" onClick={resetFilters}>초기화</button>
        </div>
      )}
    </div>
  )
}
