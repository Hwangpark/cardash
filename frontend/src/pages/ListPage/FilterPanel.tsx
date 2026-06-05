import type { CarFilterOptions, CarFilterValue, CarFilters } from '../../types/car'
import { FALLBACK_MAKES, REGION_OPTIONS } from './filterOptions'

interface Props {
  options?: CarFilterOptions
  filters: CarFilters
  setFilter: (key: keyof CarFilters, value: CarFilterValue) => void
  setFilterValues: (patch: Partial<CarFilters>) => void
}

function Select({
  value, placeholder, options, disabled, onChange,
}: {
  value?: string; placeholder: string
  options: string[]; disabled?: boolean
  onChange: (v: string | undefined) => void
}) {
  return (
    <select disabled={disabled} value={value ?? ''} onChange={e => onChange(e.target.value || undefined)}>
      <option value="">{placeholder}</option>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

function NumberInput({ placeholder, value, onChange }: {
  placeholder: string; value?: number; onChange: (v: number | undefined) => void
}) {
  return (
    <input
      type="number" placeholder={placeholder} value={value ?? ''}
      onChange={e => onChange(e.target.value ? Number(e.target.value) : undefined)}
    />
  )
}

export default function FilterPanel({ options, filters, setFilter, setFilterValues }: Props) {
  const brands = options?.brands ?? FALLBACK_MAKES
  const modelGroups = filters.brand ? (options?.model_groups[filters.brand] ?? []) : []

  const onBrandChange = (brand: string | undefined) =>
    setFilterValues({ brand, model_group: undefined, model: undefined })

  const onModelGroupChange = (model_group: string | undefined) =>
    setFilterValues({ model_group, model: undefined })

  return (
    <div className="filter-bar">
      <Select placeholder="제조사 전체" options={brands} value={filters.brand} onChange={onBrandChange} />
      <Select placeholder="모델 그룹" options={modelGroups} value={filters.model_group}
        disabled={!filters.brand || modelGroups.length === 0} onChange={onModelGroupChange} />
      <NumberInput placeholder="최소 연식" value={filters.year_min} onChange={v => setFilter('year_min', v)} />
      <NumberInput placeholder="최대 연식" value={filters.year_max} onChange={v => setFilter('year_max', v)} />
      <NumberInput placeholder="최저가 (만원)" value={filters.price_min} onChange={v => setFilter('price_min', v)} />
      <NumberInput placeholder="최고가 (만원)" value={filters.price_max} onChange={v => setFilter('price_max', v)} />
      <NumberInput placeholder="최대 주행거리" value={filters.mileage_max} onChange={v => setFilter('mileage_max', v)} />
      <Select placeholder="지역 전체" options={REGION_OPTIONS} value={filters.region} onChange={v => setFilter('region', v)} />
    </div>
  )
}
