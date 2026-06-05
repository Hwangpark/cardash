import { useQuery } from '@tanstack/react-query'
import { fetchFilterOptions } from '../../api/cars'

export const useCarCategories = (platform = 'encar') => {
  return useQuery({
    queryKey: ['filter-options', platform],
    queryFn: () => fetchFilterOptions(platform),
    staleTime: 10 * 60 * 1000,
    retry: false,
  })
}
