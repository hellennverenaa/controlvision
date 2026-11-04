/** E1.5 — testes do fluxo real de comparação (sem instalar SAM 2 ou browser).
 *
 * Node 20+ executa node:test e o TypeScript já presente no projeto transpila
 * apenas o módulo de comparação. A compilação Vue continua em npm run build.
 */
import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import {resolve, dirname} from 'node:path'
import {deflateSync} from 'node:zlib'
import assert from 'node:assert/strict'
import test from 'node:test'
import ts from 'typescript'

const here = dirname(fileURLToPath(import.meta.url))
const source = readFileSync(resolve(here, '../src/segmentationComparison.ts'), 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: {target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ES2020},
  reportDiagnostics: true,
})
assert.equal(compiled.diagnostics?.length ?? 0, 0)
const moduleUrl = 'data:text/javascript;base64,' + Buffer.from(compiled.outputText).toString('base64')
const {validateSegmentationResult, createSegmentationComparisonRunner,
       requestSegmentationMask, segmentationMaskSrc} = await import(moduleUrl)

// Cria um PNG cinza válido de 2x2, sem bibliotecas externas de imagem.
function crc32(buffer) {
  let value = 0xffffffff
  for (const byte of buffer) {
    value ^= byte
    for (let n=0; n<8; n++) value = value & 1 ? (value >>> 1) ^ 0xedb88320 : value >>> 1
  }
  return (value ^ 0xffffffff) >>> 0
}
function chunk(type, data) {
  const kind = Buffer.from(type, 'ascii')
  const length = Buffer.alloc(4)
  length.writeUInt32BE(data.length)
  const checksum = Buffer.alloc(4)
  checksum.writeUInt32BE(crc32(Buffer.concat([kind, data])))
  return Buffer.concat([length, kind, data, checksum])
}
const png = (() => {
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(2, 0)
  ihdr.writeUInt32BE(2, 4)
  ihdr[8] = 8
  ihdr[9] = 0 // grayscale
  const raw = Buffer.from([0, 0, 255, 0, 255, 0])
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw)),
    chunk('IEND', Buffer.alloc(0)),
  ]).toString('base64')
})()

function payload(method='opencv', status='ok') {
  const ok = status==='ok'
  return {
    schema_version: '1.0',
    status,
    method: method==='opencv' ? 'opencv_baseline' : 'sam2_optional',
    image_size_px: [2, 2],
    mask_png_base64: ok ? png : null,
    mask_mime_type: 'image/png',
    mask_origin: method==='opencv' ? 'poligono_externo_preenchido_do_opencv_atual' : 'sam2_caixa_derivada_do_contorno_opencv',
    contour_px: ok ? [[0,0],[1,0],[1,1],[0,1]] : [],
    foreground_pixels: ok ? 2 : 0,
    elapsed_ms: 12.5,
    prompt_used: method==='sam2' && ok,
    model_version: method==='sam2' && ok ? 'sam2.1_tiny:test.pt' : null,
    calibrated: false,
    requires_human_review: true,
    warnings: status==='indisponivel' ? ['SAM 2 desativado.'] : [],
  }
}
function response(body, status=200) {
  return new Response(typeof body==='string' ? body : JSON.stringify(body), {
    status, headers:{'Content-Type':'application/json'},
  })
}
const file = new Blob(['foto-experimental'], {type:'image/png'})

test('recebe OpenCV ok e SAM 2 desativado sem fabricar máscara de IA', async () => {
  const requests = []
  const fetcher = async (url, init) => {
    assert.equal(url, '/api/vision/segmentation/preview')
    assert.equal(init.method, 'POST')
    const data = init.body
    const method = data.get('method')
    requests.push({method, mode:data.get('mode'),tone:data.get('piece_tone'), file:data.get('file')})
    return response(payload(method, method==='sam2'?'indisponivel':'ok'))
  }
  const runner = createSegmentationComparisonRunner(fetcher)
  const result = await runner.compare(file, 'holes','light')
  assert.deepEqual(requests.map(x=>x.method).sort(), ['opencv','sam2'])
  assert.ok(requests.every(x=>x.mode==='holes' && x.tone==='light'))
  assert.ok(requests.every(x=>x.file.size===file.size && x.file.type===file.type))
  assert.equal(result.opencv.result.status, 'ok')
  assert.ok(segmentationMaskSrc(result.opencv.result)?.startsWith('data:image/png;base64,'))
  assert.equal(result.sam2.result.status, 'indisponivel')
  assert.equal(result.sam2.result.mask_png_base64, null)
  assert.equal(segmentationMaskSrc(result.sam2.result), null)
  assert.equal(result.opencv.error, null)
  assert.equal(result.sam2.error, null)
})

test('preserva diagnóstico OpenCV se a chamada do SAM 2 falhar', async () => {
  const runner=createSegmentationComparisonRunner(async (_url,init)=>
    init.body.get('method')==='sam2'
      ? response({detail:'Servidor de IA indisponível'},503)
      : response(payload('opencv'))
  )
  const result=await runner.compare(file,'holes','light')
  assert.equal(result.opencv.result.status,'ok')
  assert.equal(result.sam2.result,null)
  assert.match(result.sam2.error,/Servidor de IA indisponível/)
})

test('preserva resultado SAM 2 mesmo se o OpenCV der erro de rede', async () => {
  const runner=createSegmentationComparisonRunner(async (_url,init)=>{
    if(init.body.get('method')==='opencv') throw new Error('Sem conexão OpenCV')
    return response(payload('sam2', 'inconclusivo'))
  })
  const result=await runner.compare(file,'marks','dark')
  assert.equal(result.opencv.result,null)
  assert.match(result.opencv.error,/Sem conexão/)
  assert.equal(result.sam2.result.status,'inconclusivo')
  assert.equal(segmentationMaskSrc(result.sam2.result),null)
})

test('rejeita falso sucesso de IA sem PNG', () => {
  const invalid={...payload('sam2'), mask_png_base64:null}
  assert.throws(()=>validateSegmentationResult(invalid,'sam2'),/máscara PNG/)
})
test('rejeita PNG de outra resolução e conteúdo não PNG', () => {
  const wrong={...payload(),image_size_px:[3,2]}
  assert.throws(()=>validateSegmentationResult(wrong,'opencv'),/máscara PNG/)
  assert.throws(()=>validateSegmentationResult({...payload(),mask_png_base64:'not-a-png'},'opencv'),/máscara PNG/)
})
test('rejeita identidade de modelo diferente do solicitado', () => {
  assert.throws(()=>validateSegmentationResult(payload('opencv'),'sam2'),/contrato v1/)
})
test('rejeita versão, tipo e campos de segurança inválidos', () => {
  assert.throws(()=>validateSegmentationResult({...payload(),schema_version:'2.0'},'opencv'),/contrato v1/)
  assert.throws(()=>validateSegmentationResult({...payload(),calibrated:true},'opencv'),/contrato v1/)
  assert.throws(()=>validateSegmentationResult({...payload(),warnings:[99]},'opencv'),/contrato v1/)
})
test('não aceita máscara em status indisponível ou inconclusivo', () => {
  for(const status of ['indisponivel','inconclusivo']){
    const invalid={...payload('sam2',status),mask_png_base64:png}
    assert.throws(()=>validateSegmentationResult(invalid,'sam2'),/não pode incluir uma máscara/)
  }
})
test('resposta JSON inválida fica em erro próprio, sem disfarce de IA', async () => {
  const panel=await requestSegmentationMask(async()=>response('{inválido'), file,'holes','light','sam2')
  assert.equal(panel.result,null)
  assert.ok(panel.error)
})

function deferred() {
  let resolvePromise
  const promise = new Promise(resolve=>{resolvePromise=resolve})
  return {promise,resolve:resolvePromise}
}
test('troca de fotografia durante processamento invalida resultados antigos', async () => {
  const pending=[deferred(),deferred()]
  let index=0
  const runner=createSegmentationComparisonRunner(()=>pending[index++].promise)
  const started=runner.compare(file,'holes','light')
  runner.invalidate() // equivalente a trocar foto/tom/molde na tela
  pending[0].resolve(response(payload('opencv')))
  pending[1].resolve(response(payload('sam2','indisponivel')))
  assert.equal(await started,null)
})
test('resposta lenta da foto antiga não substitui comparação nova', async () => {
  const old=[deferred(),deferred()]
  let count=0
  const runner=createSegmentationComparisonRunner(async (_url,init)=>{
    const index=count++
    if(index<2)return old[index].promise
    return response(payload(init.body.get('method'), init.body.get('method')==='sam2'?'indisponivel':'ok'))
  })
  const older=runner.compare(file,'holes','light')
  runner.invalidate()
  const newer=await runner.compare(file,'holes','dark')
  assert.equal(newer.opencv.result.status,'ok')
  old[0].resolve(response(payload('opencv')))
  old[1].resolve(response(payload('sam2','indisponivel')))
  assert.equal(await older,null)
  assert.equal(newer.sam2.result.status,'indisponivel')
})
test('segunda comparação cancela logicamente a primeira sem misturar painéis',async()=>{
  const slow=[deferred(),deferred()]
  let count=0
  const runner=createSegmentationComparisonRunner(async (_url,init)=>{
    if(count++<2) return slow[count-1].promise
    return response(payload(init.body.get('method'),'indisponivel'))
  })
  const previous=runner.compare(file,'holes','light')
  const latest=await runner.compare(file,'marks','dark')
  assert.equal(latest.opencv.result.status,'indisponivel')
  slow[0].resolve(response(payload('opencv')))
  slow[1].resolve(response(payload('sam2')))
  assert.equal(await previous,null)
})
