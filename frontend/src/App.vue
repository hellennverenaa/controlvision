<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'

type Feature = { id: string; points: number[][]; center: number[]; shape: 'circular'|'recorte'; suggestion: string; classification: 'pendente'|'vazador'|'referencia'|'ignorar' }
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
const highlightedFeatureId = ref<string|null>(null)
let stream: MediaStream|null = null

const filtered = computed(() => (catalog.value?.pieces ?? []).filter(p =>
  (p.name + ' ' + p.id + ' ' + (p.size ?? '')).toLowerCase().includes(search.value.toLowerCase())
))
const selected = computed(() => catalog.value?.pieces.find(p => p.id === selectedId.value) ?? null)
const pendingFeatures = computed(() => selected.value?.features.filter(f => f.classification === 'pendente').length ?? 0)
const confirmedFeatures = computed(() => selected.value?.features.filter(f => f.classification === 'vazador').length ?? 0)
const suggestedHoles = computed(() => selected.value?.features.filter(f => f.shape === 'circular').length ?? 0)
function confirmCircles(): void { selected.value?.features.filter(f => f.shape === 'circular').forEach(f => { f.classification = 'vazador' }) }
function markerRadius(piece: Piece|null): number { if(!piece)return 2; return Math.max(...[piece.bbox[2]-piece.bbox[0],piece.bbox[3]-piece.bbox[1]],1)*.021 }
function flipY(viewBox: string): string {
  const [, y, , height] = viewBox.split(' ').map(Number)
  return 'translate(0 ' + (2*y + height) + ') scale(1 -1)'
}
function goToPhoto(): void { document.getElementById('etapa-foto')?.scrollIntoView({behavior:'smooth',block:'start'}) }
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
    highlightedFeatureId.value=null
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
      <nav class="workflow" aria-label="Etapas da validação">
        <div :class="['workflow-step',catalog?'done':'current']"><span>1</span><strong>Importar CAD</strong><small>DXF / HPGL</small></div>
        <div :class="['workflow-step',selected?'current':'']"><span>2</span><strong>Conferir vazadores</strong><small>Validar candidatos</small></div>
        <div :class="['workflow-step',preview?'done':'']"><span>3</span><strong>Testar imagem</strong><small>Webcam ou foto</small></div>
        <div class="workflow-step locked"><span>4</span><strong>Comparar em mm</strong><small>Fase posterior</small></div>
      </nav>
      <section class="intro">
        <div><span class="eyebrow">VALIDAÇÃO GEOMÉTRICA</span><h1>Inspeção digital de peças cortadas</h1><p><strong>1.</strong> Importe o CAD. <strong>2.</strong> Confira a peça e seus candidatos a vazadores. <strong>3.</strong> Teste a captura de imagem. A medição CAD × peça ainda não está disponível.</p></div>
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
          <section class="panel" id="etapa-cad">
            <div class="panel-title"><div><span class="eyebrow">ETAPA 2 · DESENHO COMPLETO</span><h2>Clique em uma peça para selecioná-la</h2></div><span class="muted">{{catalog?.format ?? 'CAD'}}</span></div>
            <div class="drawing">
              <svg :viewBox="overviewBox" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Visão geral das peças">
                <g :transform="flipY(overviewBox)">
                  <g v-for="piece in catalog?.pieces ?? []" :key="piece.id">
                    <polygon :points="pointsToSvg(piece.points)" :class="['shape',selectedId===piece.id?'selected':'']" @click="selectedId=piece.id"/>
                    <g v-for="feature in piece.features" :key="feature.id" @click="selectedId=piece.id">
                      <polygon :points="pointsToSvg(feature.points)" class="feature"/>
                      <circle :cx="feature.center[0]" :cy="feature.center[1]" :r="markerRadius(piece)" class="candidate-marker"/>
                    </g>
                  </g>
                </g>
              </svg>
              <div v-if="!catalog" class="placeholder">O desenho aparecerá após a importação.</div>
            </div>
          </section>
          <section class="panel">
            <div class="panel-title"><div><span class="eyebrow">ETAPA 2 · CONFERIR GEOMETRIAS INTERNAS</span><h2>{{selected?.name ?? 'Selecione uma peça'}}</h2></div><span class="muted">{{selected?.area_mm2 ?? '—'}} unidades² CAD</span></div>
            <div v-if="selected" class="review-banner">
              <strong>{{selected.features.length}} geometrias internas • {{suggestedHoles}} possíveis vazadores circulares • {{confirmedFeatures}} confirmados</strong>
              <span>{{pendingFeatures ? 'Verifique cada círculo no desenho e confirme sua função.' : 'Classificações revisadas nesta sessão. Ainda sem validação dimensional.'}}</span>
            </div>
            <div class="details">
              <svg :viewBox="detailBox" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Detalhes da peça e candidatos a vazadores">
                <g :transform="flipY(detailBox)">
                  <polygon v-if="selected" :points="pointsToSvg(selected.points)" class="shape selected"/>
                  <g v-for="feature in selected?.features ?? []" :key="feature.id">
                    <polygon :points="pointsToSvg(feature.points)" :class="['feature',feature.classification==='vazador'?'confirmed':'']"/>
                    <circle :cx="feature.center[0]" :cy="feature.center[1]" :r="markerRadius(selected)"
                      :class="['candidate-marker',feature.classification==='vazador'?'confirmed':'',highlightedFeatureId===feature.id?'highlight':'']" />
                  </g>
                </g>
              </svg>
              <div class="features"><span class="eyebrow">GEOMETRIAS INTERNAS — CONFERÊNCIA</span>
                <p class="note">Os círculos destacados são <b>candidatos</b>, não vazadores confirmados automaticamente.</p>
                <p v-if="!selected?.features.length" class="muted">Nenhuma geometria interna identificada.</p>
                <label v-for="feature in selected?.features ?? []" :key="feature.id" class="feature-item"
                  @mouseenter="highlightedFeatureId=feature.id" @mouseleave="highlightedFeatureId=null">
                  <span class="feature-description"><strong>{{feature.id}} · {{feature.shape==='circular'?'Círculo':'Recorte'}}</strong><small>{{feature.suggestion}}</small></span>
                  <select v-model="feature.classification" :aria-label="'Classificação de '+feature.id">
                    <option value="pendente">Pendente</option><option value="vazador">Vazador confirmado</option><option value="referencia">Marca/referência</option><option value="ignorar">Ignorar</option>
                  </select>
                </label>
                <button v-if="suggestedHoles" class="button secondary confirm-button" @click="confirmCircles">Confirmar círculos como vazadores</button>
                <p class="note">Marcadores ampliados apenas para facilitar a visualização. A geometria original não é alterada. Confirmações são temporárias.</p>
              </div>
            </div>
          </section>
        </div>
      </div>
      <div v-if="selected" class="next-step">
        <div><strong>Próximo passo: testar uma fotografia da peça selecionada</strong>
        <p>Idealmente, use a peça realmente cortada, plana, sobre fundo uniforme e sem mãos ou marcas desenhadas. O sistema ainda não mede a diferença com o CAD.</p></div>
        <button class="button primary" @click="goToPhoto">Ir para teste de imagem ↓</button>
      </div>
      <section class="panel camera" id="etapa-foto">
        <div class="panel-title"><div><span class="eyebrow">ETAPA 3 · IMAGEM EXPERIMENTAL</span><h2>Visualizar o contorno detectado na fotografia</h2></div><span class="tag small">PIXELS — SEM COMPARAÇÃO</span></div>
        <div class="image-guide">A borda vermelha mostra apenas o contorno detectado na foto. <strong>Não significa que corresponde à peça do DXF.</strong> Fotos de desenhos no papel testam detecção de traços; para testar cortes, fotografe uma peça recortada.</div>
        <div class="actions">
          <label class="button secondary">Enviar fotografia<input type="file" accept="image/*" hidden @change="uploadPhoto"></label>
          <button class="button secondary" @click="cameraOn?stopCamera():startCamera()">{{cameraOn?'Desligar câmera':'Abrir webcam'}}</button>
          <button v-if="cameraOn" class="button primary" @click="photograph">Fotografar</button>
        </div>
        <video v-if="cameraOn" ref="video" autoplay muted playsinline class="video"></video>
        <div class="photo-grid">
          <div class="photo" v-if="photoUrl"><img :src="photoUrl" alt="Fotografia enviada"><svg v-if="preview" :viewBox="'0 0 '+preview.image_size[0]+' '+preview.image_size[1]" preserveAspectRatio="none"><polygon :points="pointsToSvg(preview.contour)"/></svg></div>
          <p v-else class="muted">Fotografe a peça com a webcam ou envie uma imagem para avaliar a extração de contorno.</p>
          <div v-if="preview" class="metrics"><strong>Contorno da fotografia destacado</strong><span>Detecção concluída em pixels.</span>
            <details><summary>Detalhes técnicos da segmentação</summary><p>{{preview.detected_regions}} contornos brutos na imagem (incluem traços, textura, fundo e ruído; não são defeitos nem vazadores confirmados).</p></details>
            <p><strong>Etapa 4 — comparação com o CAD:</strong> ainda não implementada. Precisamos validar os vazadores físicos, o alinhamento e a calibração antes de mostrar desvios em milímetros.</p></div>
        </div>
      </section>
    </main>
    <footer>ControlVision 0.1 · Protótipo de engenharia · Nenhuma aprovação ou reprovação industrial</footer>
  </div>
</template>
