export const FALLBACK_MAKES = [
  '현대', '기아', '제네시스',
  '쉐보레(GM대우)', '르노코리아(삼성)', 'KG모빌리티(쌍용)',
  'BMW', '벤츠', '아우디', '볼보', '미니', '포르쉐', '렉서스',
]

export const REGION_OPTIONS = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '충남', '경남']

export const GRADE_OPTIONS = [
  { label: 'S 이상',  value: 'S' },
  { label: 'A+ 이상', value: 'A+' },
  { label: 'A 이상',  value: 'A' },
  { label: 'B 이상',  value: 'B' },
  { label: 'C 이상',  value: 'C' },
  { label: 'D 이상',  value: 'D' },
]

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
  { label: '5천km 이하',  value: 5000 },
  { label: '1만km 이하',  value: 10000 },
  { label: '2만km 이하',  value: 20000 },
  { label: '3만km 이하',  value: 30000 },
  { label: '4만km 이하',  value: 40000 },
  { label: '5만km 이하',  value: 50000 },
  { label: '6만km 이하',  value: 60000 },
  { label: '7만km 이하',  value: 70000 },
  { label: '8만km 이하',  value: 80000 },
  { label: '10만km 이하', value: 100000 },
  { label: '12만km 이하', value: 120000 },
  { label: '15만km 이하', value: 150000 },
  { label: '20만km 이하', value: 200000 },
]

export const PRICE_OPTIONS = [
  { label: '500만 이하',  value: 500 },
  { label: '700만 이하',  value: 700 },
  { label: '1000만 이하', value: 1000 },
  { label: '1200만 이하', value: 1200 },
  { label: '1500만 이하', value: 1500 },
  { label: '1800만 이하', value: 1800 },
  { label: '2000만 이하', value: 2000 },
  { label: '2100만 이하', value: 2100 },
  { label: '2200만 이하', value: 2200 },
  { label: '2300만 이하', value: 2300 },
  { label: '2400만 이하', value: 2400 },
  { label: '2500만 이하', value: 2500 },
  { label: '2600만 이하', value: 2600 },
  { label: '2700만 이하', value: 2700 },
  { label: '2800만 이하', value: 2800 },
  { label: '2900만 이하', value: 2900 },
  { label: '3000만 이하', value: 3000 },
  { label: '3500만 이하', value: 3500 },
  { label: '4000만 이하', value: 4000 },
  { label: '5000만 이하', value: 5000 },
  { label: '6000만 이하', value: 6000 },
  { label: '7000만 이하', value: 7000 },
  { label: '8000만 이하', value: 8000 },
  { label: '1억 이하',    value: 10000 },
]

const thisYear = new Date().getFullYear()
export const YEAR_OPTIONS = Array.from({ length: thisYear - 2004 }, (_, i) => thisYear - i)
