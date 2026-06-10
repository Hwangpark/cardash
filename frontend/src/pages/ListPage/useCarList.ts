import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { fetchCars } from '../../api/cars'
import type { CarFilterValue, CarFilters } from '../../types/car'

const NUM_KEYS = new Set<keyof CarFilters>(['year_min', 'year_max', 'price_min', 'price_max', 'mileage_max', 'owner_changes_max', 'page', 'size'])

const DEFAULT_PARAMS = { brand: '제네시스', model_group: 'G70', page: '1', size: '20' }

const parseFilters = (params: URLSearchParams): CarFilters => {
  const filters: CarFilters = { page: 1, size: 20 }
  const rec = filters as Record<string, unknown>
  params.forEach((value, key) => {
    rec[key] = NUM_KEYS.has(key as keyof CarFilters) ? Number(value) : value
  })
  return filters
}

export const useCarList = () => {
  const [searchParams, setSearchParams] = useSearchParams()

  useEffect(() => {
    if (!searchParams.has('brand')) {
      setSearchParams(DEFAULT_PARAMS, { replace: true })
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const filters = parseFilters(searchParams)

  const query = useQuery({
    queryKey: ['cars', Object.fromEntries(searchParams)],
    queryFn: () => fetchCars(filters),
    placeholderData: prev => prev,
    enabled: searchParams.has('brand'),
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

  const resetFilters = () => setSearchParams(DEFAULT_PARAMS, { replace: true })

  return { ...query, filters, setFilter, setFilterValues, setPage, resetFilters }
}
