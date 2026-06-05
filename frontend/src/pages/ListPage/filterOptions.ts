export const FALLBACK_MAKES = ['현대', '기아', '쉐보레(GM대우)', '르노코리아(삼성)', 'BMW', '벤츠', '아우디', '볼보']

export const REGION_OPTIONS = ['서울', '경기', '인천', '부산', '대구', '광주', '대전']

export const PLATFORM_OPTIONS = [
  { value: 'encar', label: '엔카' },
  { value: 'kcar', label: '케이카' },
  { value: 'kbchachacha', label: 'KB차차차' },
  { value: 'bobaedream', label: '보배드림' },
]

export const PLATFORM_LABEL = PLATFORM_OPTIONS.reduce<Record<string, string>>((acc, option) => {
  acc[option.value] = option.label
  return acc
}, {})

export const getPlatformLabel = (platform: string) => {
  return PLATFORM_LABEL[platform] ?? platform
}
