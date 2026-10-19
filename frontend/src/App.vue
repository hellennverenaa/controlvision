<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'

type Feature = { id: string; points: number[][]; classification: 'pendente'|'vazador'|'referencia'|'ignorar' }
type Piece = { id: string; name: string; size: string|null; points: number[][]; features: Feature[]; bbox: number[]; area_mm2: number }
type Catalog = { filename: string; format: string; units: string; count: number; pieces: Piece[]; warnings: string[] }
type Preview = { status: string; contour: number[][]; image_size: number[]; detected_regions: number }

const catalog = ref<Catalog|null>(null)
const selectedId = ref<string|null>(null)
const search = ref('')
const busy = ref(false)
const error = ref('')
const photoUrl = ref('')
const preview = ref<Preview|null>(null)
const video = ref<HTMLVideoElement|null>(null)
const cameraOn = ref(false)
let stream: MediaStream|null = null

const filtered = computed(() => (catalog.value?.pieces ?? []).filter(p =>
  (p.name + ' ' + p.id + ' ' + (p.size ?? '')).toLowerCase().includes(search.value.toLowerCase())
))
const selected = computed(() => catalog.value?.pieces.find(p => p.id === selectedId.value) ?? null)
function pointsToSvg(points: number[][]): string { return points.map(p => p.join(',')).join(' ') }
function fitBox(values: number[][]): string {
  if (!values.length) return '0 0 400 300'
  let x0=Infinity, y0=Infinity, x1=-Infinity, y1=-Infinity
  for (const [x,y] of values) { x0=Math.min(x0,x); y0=Math.min(y0,y); x1=Math.max(x1,x); y1=Math.max(y1,y) }
  const pad=Math.max(6,Math.max(x1-x0,y1-y0)*.04)
  return [x0-pad,y0-pad,x1-x0+pad*2,y1-y0+pad*2].join(' ')
}
const overviewBox = computed(() => fitBox((catalog.value?.pieces ?? []).flatMap(p => p.points)))
const detailBox = computed(() => fitBox(selected.value?.points ?? []))

async function importFile(event: Event): Promise<void> {
  const file=(event.target as HTMLInputElement).files?.[0]
  if (!file) return
  busy.value=true; error.value=''; catalog.value=null; selectedId.value=null
  try {
    const form=new FormData(); form.append('file',file)
    const response=await fetch('/api/cad/import',{method:'POST',body:form})
    const body=await response.json()
    if (!response.ok) throw Error(body.detail ?? 'Não foi possível importar.')
    catalog.value=body as Catalog
    selectedId.value=catalog.value.pieces[0]?.id ?? null
  } catch (e) { error.value=e instanceof Error?e.message:'Erro inesperado' }
  finally { busy.value=false }
}

async function processPhoto(file: File): Promise<void> {
  preview.value=null;error.value='';busy.value=true
  if(photoUrl.value) URL.revokeObjectURL(photoUrl.value)
  photoUrl.value=URL.createObjectURL(file)
  try {
    const form=new FormData();form.append('file',file)
    const response=await fetch('/api/vision/preview',{method:'POST',body:form})
    const result=await response.json()
    if (!response.ok) throw Error(result.detail ?? 'Falha ao analisar imagem.')
    preview.value=result as Preview
  } catch(e) { error.value=e instanceof Error?e.message:'Erro inesperado' }
  finally { busy.value=false }
}
function uploadPhoto(event: Event): void {
  const file=(event.target as HTMLInputElement).files?.[0]
  if(file) void processPhoto(file)
}
async function startCamera(): Promise<void> {
  error.value=''
  try {
    stream=await navigator.mediaDevices.getUserMedia({video:true,audio:false})
    cameraOn.value=true
    await nextTick()
    if(video.value) video.value.srcObject=stream
  } catch { error.value='Câmera indisponível: utilize localhost/HTTPS ou envie uma fotografia.' }
}
function stopCamera(): void {stream?.getTracks().forEach(t=>t.stop()); stream=null;cameraOn.value=false}
function photograph(): void {
  if(!video.value || !video.value.videoWidth) return
  const canvas=document.createElement('canvas')
  canvas.width=video.value.videoWidth;canvas.height=video.value.videoHeight
  canvas.getContext('2d')?.drawImage(video.value,0,0)
  canvas.toBlob(blob=>{if(blob) void processPhoto(new File([blob],'captura.png',{type:'image/png'}))},'image/png')
}
onBeforeUnmount(()=>{stopCamera();if(photoUrl.value)URL.revokeObjectURL(photoUrl.value)})
</script>

<template>
  <div class="app">
    <header>
      <div class="brand"><span class="logo">CV</span><div><strong>ControlVision</strong><small>Inspeção dimensional · Laboratório</small></div></div>
      <span class="tag">PROTÓTIPO — NÃO LIBERA PRODUÇÃO</span>
    </header>
    <main>
      <section class="intro">
        <div><span class="eyebrow">VALIDAÇÃO GEOMÉTRICA</span><h1>Inspeção digital de peças cortadas</h1><p>Importe um arquivo CAD, selecione peças no desenho ou na lista e teste a detecção de contornos em fotografias.</p></div>
        <label class="button primary">{{busy?'Processando…':'Importar DXF / HPGL'}}<input type="file" accept=".dxf,.hpgl,.plt,.hp2" hidden :disabled="busy" @change="importFile"></label>
      </section>
      <div v-if="error" class="alert error">{{ error }}</div>
      <div v-if="catalog?.warnings.length" class="alert"><strong>Revisão obrigatória:</strong> {{ catalog.warnings.join(' · ') }}</div>
      <div class="layout">
        <aside class="panel">
          <div class="panel-title"><div><span class="eyebrow">ARQUIVO ATUAL</span><h2>{{ catalog?.filename ?? 'Nenhum CAD importado' }}</h2></div><span class="counter">{{catalog?.count ?? 0}}</span></div>
          <input v-model="search" class="search" type="search" placeholder="Buscar peça ou tamanho..." aria-label="Buscar peça">
          <div class="items">
            <button v-for="piece in filtered" :key="piece.id" :class="['item',selectedId===piece.id?'active':'']" @click="selectedId=piece.id">
              <span class="piece-id">{{piece.id}}</span><span><strong>{{piece.name}}</strong><small>{{piece.size ? 'Nº '+piece.size+' • ' : ''}}{{piece.features.length}} internos</small></span><b>›</b>
            </button>
            <p v-if="!filtered.length" class="muted">{{ catalog ? 'Nenhuma peça encontrada.' : 'Importe um CAD para começar.' }}</p>
          </div>
        </aside>
        <div class="workspace">
          <section class="panel">
            <div class="panel-title"><div><span class="eyebrow">DESENHO COMPLETO</span><h2>Clique em uma peça para selecioná-la</h2></div><span class="muted">{{catalog?.format ?? 'CAD'}}</span></div>
            <div class="drawing">
              <svg :viewBox="overviewBox" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Visão geral das peças">
                <g v-for="piece in catalog?.pieces ?? []" :key="piece.id">
                  <polygon :points="pointsToSvg(piece.points)" :class="['shape',selectedId===piece.id?'selected':'']" @click="selectedId=piece.id"/>
                  <polygon v-for="feature in piece.features" :key="feature.id" :points="pointsToSvg(feature.points)" class="feature"/>
                </g>
              </svg>
              <div v-if="!catalog" class="placeholder">O desenho aparecerá após a importação.</div>
            </div>
          </section>
          <section class="panel">
            <div class="panel-title"><div><span class="eyebrow">DETALHES</span><h2>{{selected?.name ?? 'Selecione uma peça'}}</h2></div><span class="muted">{{selected?.area_mm2 ?? '—'}} mm²</span></div>
            <div class="details">
              <svg :viewBox="detailBox" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Detalhes da peça">
                <polygon v-if="selected" :points="pointsToSvg(selected.points)" class="shape selected"/>
                <polygon v-for="feature in selected?.features ?? []" :key="feature.id" :points="pointsToSvg(feature.points)" :class="['feature',feature.classification==='vazador'?'confirmed':'']"/>
              </svg>
              <div class="features"><span class="eyebrow">GEOMETRIAS INTERNAS</span>
                <p v-if="!selected?.features.length" class="muted">Nenhuma geometria interna identificada.</p>
                <label v-for="feature in selected?.features ?? []" :key="feature.id">
                  <span>{{feature.id}}</span>
                  <select v-model="feature.classification" aria-label="Classificação da geometria">
                    <option value="pendente">Pendente</option><option value="vazador">Vazador</option><option value="referencia">Referência</option><option value="ignorar">Ignorar</option>
                  </select>
                </label>
                <p class="note">Classificação provisória nesta sessão. O CAD original não é alterado.</p>
              </div>
            </div>
          </section>
        </div>
      </div>
      <section class="panel camera">
        <div class="panel-title"><div><span class="eyebrow">IMAGEM EXPERIMENTAL</span><h2>Extrair contorno de fotografia</h2></div><span class="tag small">PIXELS — SEM CALIBRAÇÃO</span></div>
        <div class="actions">
          <label class="button secondary">Enviar fotografia<input type="file" accept="image/*" hidden @change="uploadPhoto"></label>
          <button class="button secondary" @click="cameraOn?stopCamera():startCamera()">{{cameraOn?'Desligar câmera':'Abrir webcam'}}</button>
          <button v-if="cameraOn" class="button primary" @click="photograph">Fotografar</button>
        </div>
        <video v-if="cameraOn" ref="video" autoplay muted playsinline class="video"></video>
        <div class="photo-grid">
          <div class="photo" v-if="photoUrl"><img :src="photoUrl" alt="Fotografia enviada"><svg v-if="preview" :viewBox="'0 0 '+preview.image_size[0]+' '+preview.image_size[1]" preserveAspectRatio="none"><polygon :points="pointsToSvg(preview.contour)"/></svg></div>
          <p v-else class="muted">Fotografe a peça com a webcam ou envie uma imagem para avaliar a extração de contorno.</p>
          <div v-if="preview" class="metrics"><strong>Contorno identificado</strong><span>Regiões identificadas: {{preview.detected_regions}}</span><p>Ainda não é uma medição dimensional. Comparação CAD × câmera, calibração e tolerâncias virão após validação.</p></div>
        </div>
      </section>
    </main>
    <footer>ControlVision 0.1 · Protótipo de engenharia · Nenhuma aprovação ou reprovação industrial</footer>
  </div>
</template>
