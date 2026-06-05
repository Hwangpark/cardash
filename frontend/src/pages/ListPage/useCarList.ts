import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchCars } from '../../api/cars'
import type { CarFilterValue, CarFilters } from '../../types/car'

const normalizeFilterValue = (value: CarFilterValue) => {
  if (typeof value === 'string') return value.trim() || undefined
  return value
}

const normalizeFilterPatch = (patch: Partial<CarFilters>) => {
  return Object.fromEntries(
    Object.entries(patch).map(([key, value]) => [key, normalizeFilterValue(value)])
  )
}

export const useCarList = () => {
  const [filters, setFilters] = useState<CarFilters>({ page: 1, size: 20 })

  const query = useQuery({
    queryKey: ['cars', filters],
    queryFn: () => fetchCars(filters),
  })

  const setFilter = (key: keyof CarFilters, value: CarFilterValue) => {
    setFilters(prev => ({ ...prev, [key]: normalizeFilterValue(value), page: 1 }))
  }

  const setFilterValues = (patch: Partial<CarFilters>) => {
    setFilters(prev => ({ ...prev, ...normalizeFilterPatch(patch), page: 1 }))
  }

  const setPage = (page: number) => setFilters(prev => ({ ...prev, page }))

  return { ...query, filters, setFilter, setFilterValues, setPage }
}
