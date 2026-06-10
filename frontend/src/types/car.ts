export interface ScoreSummary {
  grade: string
  /** true = 무사고, false = 사고이력 있음, null = 보험 데이터 없어 미지 */
  accident_free: boolean | null
  owner_change_count: number | null
}

export interface Car {
  id: number
  platform: string
  external_id: string
  brand: string | null
  model_group: string | null
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
  /** 목록 응답에서만 채워짐 — 미채점 차량은 null */
  score_summary?: ScoreSummary | null
}

export interface AccidentRecord {
  date: string | null
  insurance_benefit: number
  part_cost: number
  labor_cost: number
  painting_cost: number
}

export type InsuranceFetchStatus =
  | 'available'
  | 'private'
  | 'viewable_unfetched'
  | 'reregistered_listing'
  | 'unavailable'
  | 'not_applicable'

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
  insurance_fetch_status: InsuranceFetchStatus
  accident_history: AccidentRecord[] | null
  owner_change_count: number | null
}

export interface CarDetail {
  car: Car
  score: Score | null
}

export interface CarListResponse {
  items: Car[]
  page: number
  size: number
  total: number
  has_next: boolean
}

/** /cars/filter-options 응답 — 필터 드롭다운용 */
export interface CarFilterOptions {
  brands: string[]
  model_groups: Record<string, string[]>   // brand → model_group 목록
  years: number[]
  regions: string[]
}

export interface CarFilters {
  platform?: string
  brand?: string
  model_group?: string
  model?: string
  year_min?: number
  year_max?: number
  price_min?: number
  price_max?: number
  mileage_max?: number
  region?: string
  /** 이 등급 이상만 (S/A+/A/B/C/D/F 중 하나) */
  grade_min?: string
  /** '1'이면 무사고만 — boolean이 CarFilterValue에 없어 문자열 컨벤션을 그대로 따름 */
  accident_free?: string
  owner_changes_max?: number
  /** '1'이면 보험이력 조회 불가 차량 제외 */
  has_insurance_data?: string
  sort?: string
  page?: number
  size?: number
}

export type CarFilterValue = string | number | undefined
