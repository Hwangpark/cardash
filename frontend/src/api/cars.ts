import client from './client'
import type { CarDetail, CarFilters, CarListResponse } from '../types/car'

export const fetchCars = async (filters: CarFilters): Promise<CarListResponse> => {
  const { data } = await client.get('/cars', { params: filters })
  return data
}

export const fetchCarDetail = async (id: number): Promise<CarDetail> => {
  const { data } = await client.get(`/cars/${id}`)
  return data
}

export const analyzeCarDetail = async (id: number): Promise<CarDetail> => {
  const { data } = await client.post(`/cars/${id}/analyze`)
  return data
}
