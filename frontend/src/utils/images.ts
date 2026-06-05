const ABSOLUTE_URL_PATTERN = /^(https?:|data:|blob:)/i
// 실제 Encar CDN: ci.encar.com/carpicture (img.encar.com 아님)
const PLATFORM_IMAGE_BASE_URL: Record<string, string> = {
  encar: 'https://ci.encar.com/carpicture',
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
