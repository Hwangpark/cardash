import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { fetchCars } from '../../api/cars'
import type { CarFilterValue, CarFilters } from '../../types/car'

const NUM_KEYS = new Set<keyof CarFilters>(['year_min', 'year_max', 'price_min', 'price_max', 'mileage_max', 'page', 'size'])

const parseFilters = (params: URLSearchParams): CarFilters => {
  const filters: CarFilters = { page: 1, size: 20 }
  params.forEach((value, key) => {
    const k = key as keyof CarFilters
    if (NUM_KEYS.has(k)) (filters as any)[k] = Number(value)
    else (filters as any)[k] = value
  })
  return filters
}

export const useCarList = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const filters = parseFilters(searchParams)

  const query = useQuery({
    queryKey: ['cars', Object.fromEntries(searchParams)],
    queryFn: () => fetchCars(filters),
    placeholderData: prev => prev,
  })

  const setFilter = (key: keyof CarFilters, value: CarFilterValue) => {
    setSearchParams(prev => {
      if (value !== undefined && value !== '') prev.set(key, String(value))
      else prev.delete(key)
      prev.set('page', '1')
      return prev
    }, { replace: true })
  }

  const setFilterValues = (patch: Partial<CarFilters>) => {
    setSearchParams(prev => {
      Object.entries(patch).forEach(([key, value]) => {
        if (value !== undefined && value !== '') prev.set(key, String(value))
        else prev.delete(key)
      })
      prev.set('page', '1')
      return prev
    }, { replace: true })
  }

  const setPage = (page: number) => {
    setSearchParams(prev => { prev.set('page', String(page)); return prev }, { replace: true })
  }

  const resetFilters = () => setSearchParams({ page: '1', size: '20' }, { replace: true })

  return { ...query, filters, setFilter, setFilterValues, setPage, resetFilters }
}
