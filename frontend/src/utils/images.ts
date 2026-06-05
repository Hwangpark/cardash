const ABSOLUTE_URL_PATTERN = /^(https?:|data:|blob:)/i
const ENCAR_IMAGE_BASE_URL = 'https://img.encar.com'
const PLATFORM_IMAGE_BASE_URL: Record<string, string> = {
  encar: ENCAR_IMAGE_BASE_URL,
}
const PROTOCOL_RELATIVE_URL_PATTERN = /^\/\//

export const resolveCarImageUrl = (imageUrl?: string | null, platform?: string) => {
  const trimmedUrl = imageUrl?.trim()
  const baseUrl = PLATFORM_IMAGE_BASE_URL[platform ?? '']

  if (!trimmedUrl) return null
  if (ABSOLUTE_URL_PATTERN.test(trimmedUrl)) return trimmedUrl
  if (PROTOCOL_RELATIVE_URL_PATTERN.test(trimmedUrl)) return `https:${trimmedUrl}`
  if (!baseUrl) return trimmedUrl

  return trimmedUrl.startsWith('/')
    ? `${baseUrl}${trimmedUrl}`
    : `${baseUrl}/${trimmedUrl}`
}
