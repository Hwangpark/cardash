export const FALLBACK_MAKES = [
  '현대', '기아', '제네시스',
  '쉐보레(GM대우)', '르노코리아(삼성)', 'KG모빌리티(쌍용)',
  'BMW', '벤츠', '아우디', '볼보', '미니', '포르쉐', '렉서스',
]

export const REGION_OPTIONS = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '충남', '경남']

export const PLATFORM_OPTIONS = [
  { value: 'encar',       label: '엔카' },
  { value: 'kcar',        label: '케이카' },
  { value: 'kbchachacha', label: 'KB차차차' },
  { value: 'bobaedream',  label: '보배드림' },
]

export const PLATFORM_LABEL = PLATFORM_OPTIONS.reduce<Record<string, string>>((acc, o) => {
  acc[o.value] = o.label; return acc
}, {})

export const getPlatformLabel = (platform: string) => PLATFORM_LABEL[platform] ?? platform

export const MILEAGE_OPTIONS = [
  { label: '1만km 이하',  value: 10000 },
  { label: '3만km 이하',  value: 30000 },
  { label: '5만km 이하',  value: 50000 },
  { label: '7만km 이하',  value: 70000 },
  { label: '10만km 이하', value: 100000 },
  { label: '15만km 이하', value: 150000 },
  { label: '20만km 이하', value: 200000 },
]

export const PRICE_OPTIONS = [
  { label: '500만 이하',  value: 500 },
  { label: '1000만 이하', value: 1000 },
  { label: '1500만 이하', value: 1500 },
  { label: '2000만 이하', value: 2000 },
  { label: '3000만 이하', value: 3000 },
  { label: '4000만 이하', value: 4000 },
  { label: '5000만 이하', value: 5000 },
]

const thisYear = new Date().getFullYear()
export const YEAR_OPTIONS = Array.from({ length: thisYear - 2004 }, (_, i) => thisYear - i)
