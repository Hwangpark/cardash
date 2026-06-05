export interface Car {
  id: number
  platform: string
  external_id: string
  brand: string | null
  model: string | null
  year: number | null
  trim: string | null
  price: number | null
  mileage: number | null
  fuel: string | null
  transmission: string | null
  color: string | null
  region: string | null
  seller_type: string | null
  images: string[] | null
  url: string | null
  crawled_at: string
}

export interface Score {
  total: number
  grade: string
  accident: number
  mileage: number
  price: number
  inspection: number
  rental: number
  owner_changes: number
  penalty: number
  no_insurance_data: boolean
}

export interface CarDetail {
  car: Car
  score: Score | null
}

export interface CarListResponse {
  items: Car[]
  page: number
  size: number
}

export interface CarFilters {
  platform?: string
  brand?: string
  model?: string
  year_min?: number
  year_max?: number
  price_min?: number
  price_max?: number
  mileage_max?: number
  region?: string
  page?: number
  size?: number
}
