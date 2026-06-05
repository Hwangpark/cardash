import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchCars } from '../../api/cars'
import type { CarFilters } from '../../types/car'

export const useCarList = () => {
  const [filters, setFilters] = useState<CarFilters>({ page: 1, size: 20 })

  const query = useQuery({
    queryKey: ['cars', filters],
    queryFn: () => fetchCars(filters),
  })

  const setFilter = (key: keyof CarFilters, value: string | number | undefined) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined, page: 1 }))
  }

  const setPage = (page: number) => setFilters(prev => ({ ...prev, page }))

  return { ...query, filters, setFilter, setPage }
}
