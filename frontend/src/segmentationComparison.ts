/** E1.5 — transporte testável e validação da comparação experimental OpenCV × SAM 2.
 *
 * O SAM 2 é opcional. Não transformar falha/inconclusão em uma máscara fictícia,
 * nem trocar o método declarado na API. Esta comparação não mede vazadores.
 */
export type SegmentationMethod = 'opencv' | 'sam2'
export type CaptureMode = 'marks' | 'holes'
export type PieceTone = 'dark' | 'light'
export type SegmentationStatus = 'ok' | 'inconclusivo' | 'indisponivel'

export type SegmentationResult = {
  schema_version: string
  status: SegmentationStatus
  method: string
  image_size_px: number[]
  mask_png_base64: string | null
  mask_mime_type: string
  mask_origin: string
  contour_px: number[][]
  foreground_pixels: number
  elapsed_ms: number
  prompt_used: boolean
  model_version: string | null
  calibrated: boolean
  requires_human_review: boolean
  warnings: string[]
}
export type SegmentationPanel = { result: SegmentationResult | null; error: string | null }
export type SegmentationComparison = { opencv: SegmentationPanel; sam2: SegmentationPanel }
type Fetcher = (input: string, init: RequestInit) => Promise<Response>

const ENDPOINT = '/api/vision/segmentation/preview'
const EXPECTED_METHOD: Record<SegmentationMethod, string> = {
  opencv: 'opencv_baseline',
  sam2: 'sam2_optional',
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Confere assinatura e dimensões do cabeçalho PNG, sem decodificar a imagem inteira.
 * Não substitui a validação de conteúdo do backend. */
function hasPngHeader(base64: string, width: number, height: number): boolean {
  if (base64.length < 44 || !/^[A-Za-z0-9+/]+={0,2}$/.test(base64)) return false
  try {
    const header = atob(base64.slice(0, 44))
    const signature = [137, 80, 78, 71, 13, 10, 26, 10]
    if (!signature.every((byte, i) => header.charCodeAt(i) === byte)) return false
    if (header.slice(12, 16) !== 'IHDR') return false
    const u32 = (i: number) => (
      (header.charCodeAt(i) * 16777216) +
      (header.charCodeAt(i + 1) << 16) +
      (header.charCodeAt(i + 2) << 8) +
      header.charCodeAt(i + 3)
    )
    return u32(16) === width && u32(20) === height
  } catch {
    return false
  }
}

export function validateSegmentationResult(
  value: unknown, requested: SegmentationMethod
): SegmentationResult {
  if (!record(value) || value.schema_version !== '1.0' ||
      value.method !== EXPECTED_METHOD[requested] ||
      !['ok', 'inconclusivo', 'indisponivel'].includes(String(value.status)) ||
      !Array.isArray(value.image_size_px) || value.image_size_px.length !== 2 ||
      !value.image_size_px.every(n => Number.isInteger(n) && n > 0) ||
      !Array.isArray(value.warnings) ||
      !value.warnings.every(s => typeof s === 'string') ||
      !Array.isArray(value.contour_px) ||
      !Number.isFinite(value.elapsed_ms) || Number(value.elapsed_ms) < 0 ||
      typeof value.foreground_pixels !== 'number' || !Number.isInteger(value.foreground_pixels) || value.foreground_pixels < 0 ||
      typeof value.prompt_used !== 'boolean' ||
      typeof value.mask_origin !== 'string' ||
      value.mask_mime_type !== 'image/png' ||
      typeof value.calibrated !== 'boolean' || value.calibrated ||
      value.requires_human_review !== true ||
      value.model_version !== null && typeof value.model_version !== 'string') {
    throw new Error('Resposta da segmentação incompatível com o contrato v1.')
  }
  const [width, height] = value.image_size_px as number[]
  if (value.status === 'ok') {
    if (typeof value.mask_png_base64 !== 'string' ||
        !hasPngHeader(value.mask_png_base64, width, height) ||
        value.contour_px.length < 3 || value.foreground_pixels <= 0) {
      throw new Error('Segmentação informou sucesso sem máscara PNG válida para a imagem.')
    }
  } else if (value.mask_png_base64 !== null || value.contour_px.length ||
             value.foreground_pixels !== 0) {
    throw new Error('Segmentação inconclusiva/indisponível não pode incluir uma máscara.')
  }
  return value as SegmentationResult
}

export function segmentationMaskSrc(result: SegmentationResult | null): string | null {
  return result?.status === 'ok' && result.mask_png_base64 &&
    result.mask_mime_type === 'image/png'
    ? 'data:image/png;base64,' + result.mask_png_base64 : null
}

export async function requestSegmentationMask(
  fetcher: Fetcher, file: File, mode: CaptureMode, tone: PieceTone,
  method: SegmentationMethod
): Promise<SegmentationPanel> {
  try {
    const body = new FormData()
    body.append('file', file)
    body.append('method', method)
    body.append('mode', mode)
    body.append('piece_tone', tone)
    const response = await fetcher(ENDPOINT, {method: 'POST', body})
    const parsed: unknown = await response.json()
    if (!response.ok) {
      const detail = record(parsed) && typeof parsed.detail === 'string' ? parsed.detail : null
      throw new Error(detail || 'Falha HTTP ao solicitar segmentação.')
    }
    return {result: validateSegmentationResult(parsed, method), error: null}
  } catch (e) {
    return {result: null, error: e instanceof Error ? e.message : 'Erro ao consultar segmentação.'}
  }
}

/** Um resultado obsoleto nunca deve chegar ao componente Vue.
 * Ambos os métodos usam o MESMO arquivo, modo e tom, mas falham de forma
 * independente: um resultado válido não some porque o outro falhou. */
export function createSegmentationComparisonRunner(fetcher: Fetcher) {
  let generation = 0
  return {
    invalidate(): void { generation += 1 },
    async compare(
      file: File, mode: CaptureMode, tone: PieceTone
    ): Promise<SegmentationComparison | null> {
      const id = ++generation
      const [opencv, sam2] = await Promise.all([
        requestSegmentationMask(fetcher, file, mode, tone, 'opencv'),
        requestSegmentationMask(fetcher, file, mode, tone, 'sam2'),
      ])
      return id === generation ? {opencv, sam2} : null
    },
  }
}
