<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

type Feature = { id: string; points: number[][]; center: number[]; shape: 'circular'|'recorte'; suggestion: string; classification: 'pendente'|'vazador'|'referencia'|'ignorar' }
type Piece = { id: string; name: string; size: string|null; points: number[][]; features: Feature[]; bbox: number[]; area_mm2: number }
type Catalog = { filename: string; format: string; units: string; count: number; pieces: Piece[]; warnings: string[] }
type PhotoCandidate = { id: string; center: number[]; radius_px: number; circularity: number; kind: string }
type Preview = { status: string; contour: number[][]; image_size: number[]; detected_regions: number; mode: 'marks'|'holes'; candidates: PhotoCandidate[]; candidate_count: number; warnings: string[] }

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
const step = ref<1|2|3>(1)
const photoMode = ref<'marks'|'holes'>('marks')
const lastPhoto = ref<File|null>(null)
function selectStep(value: 1|2|3): void {
  if (value===2 && !catalog.value) return
  if (value===3 && !selected.value) return
  step.value=value
  window.scrollTo({top:0,behavior:'smooth'})
}
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
function goToPhoto(): void { selectStep(3) }
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
    step.value=2
  } catch (e) { error.value=e instanceof Error?e.message:'Erro inesperado' }
  finally { busy.value=false }
}

async function processPhoto(file: File): Promise<void> {
  lastPhoto.value=file
  preview.value=null;error.value='';busy.value=true
  if(photoUrl.value) URL.revokeObjectURL(photoUrl.value)
  photoUrl.value=URL.createObjectURL(file)
  try {
    const form=new FormData();form.append('file',file);form.append('mode',photoMode.value)
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
watch(photoMode, () => { if(lastPhoto.value) void processPhoto(lastPhoto.value) })
watch(selectedId, () => {preview.value=null;lastPhoto.value=null;if(photoUrl.value)URL.revokeObjectURL(photoUrl.value);photoUrl.value='' })
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
        <button type="button" :class="['workflow-step',step===1?'current':'',catalog?'done':'']" :aria-current="step===1?'step':undefined" @click="selectStep(1)"><span>1</span><strong>Importar CAD</strong><small>DXF / HPGL</small></button>
        <button type="button" :disabled="!catalog" :class="['workflow-step',step===2?'current':'']" :aria-current="step===2?'step':undefined" @click="selectStep(2)"><span>2</span><strong>Conferir vazadores</strong><small>Revisar candidatos</small></button>
        <button type="button" :disabled="!selected" :class="['workflow-step',step===3?'current':'',preview?'done':'']" :aria-current="step===3?'step':undefined" @click="selectStep(3)"><span>3</span><strong>Analisar fotografia</strong><small>Pontos e aberturas</small></button>
        <div class="workflow-step locked"><span>4</span><strong>Comparar em mm</strong><small>Em desenvolvimento</small></div>
      </nav>
      <section v-if="step===1" class="intro">
        <div><span class="eyebrow">VALIDAÇÃO GEOMÉTRICA</span><h1>Inspeção digital de peças cortadas</h1><p><strong>1.</strong> Importe o CAD. <strong>2.</strong> Confira a peça e seus candidatos a vazadores. <strong>3.</strong> Teste a captura de imagem. A medição CAD × peça ainda não está disponível.</p></div>
        <label class="button primary">{{busy?'Processando…':'Importar DXF / HPGL'}}<input type="file" accept=".dxf,.hpgl,.plt,.hp2" hidden :disabled="busy" @change="importFile"></label>
      </section>
      <div v-if="error" class="alert error">{{ error }}</div>
      <div v-if="step===2 && catalog?.warnings.length" class="alert"><strong>Revisão obrigatória:</strong> {{ catalog.warnings.join(' · ') }}</div>
      <div v-if="step===1" class="panel start-panel">
        <h2>Como usar o protótipo</h2>
        <p>Comece importando um desenho CAD. O sistema abrirá automaticamente a <strong>Etapa 2</strong>, para conferir os candidatos a vazadores. Após isso, clique em <strong>Continuar para a Etapa 3</strong> para analisar uma fotografia.</p>
        <p class="note">A quarta etapa, de comparação dimensional em milímetros, ainda não está implementada.</p>
      </div>
      <div v-if="step===2" class="layout">
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
      <div v-if="step===2 && selected" class="next-step">
        <div><strong>Próximo passo: testar uma fotografia da peça selecionada</strong>
        <p>Idealmente, use a peça realmente cortada, plana, sobre fundo uniforme e sem mãos ou marcas desenhadas. O sistema ainda não mede a diferença com o CAD.</p></div>
        <button class="button primary" @click="goToPhoto">Continuar para Etapa 3 →</button>
      </div>
      <section v-if="step===3" class="panel camera" id="etapa-foto">
        <div class="panel-title"><div><span class="eyebrow">ETAPA 3 · IMAGEM EXPERIMENTAL</span><h2>Visualizar o contorno detectado na fotografia</h2></div><span class="tag small">PIXELS — SEM COMPARAÇÃO</span></div>
        <div class="image-guide"><strong>Peça selecionada no CAD: {{selected?.name}}</strong> • {{confirmedFeatures}} vazadores confirmados no CAD.
          <br>A borda vermelha é só o contorno detectado na foto. Os círculos amarelos serão <strong>candidatos visuais</strong>; ainda não há alinhamento CAD × imagem.</div>
        <div class="photo-controls">
          <strong>O que está sendo fotografado?</strong>
          <label><input v-model="photoMode" type="radio" value="marks"> Desenho no papel com pontos escuros</label>
          <label><input v-model="photoMode" type="radio" value="holes"> Peça cortada com furos claros e fundo contrastante</label>
          <p class="note">{{photoMode==='marks'?'O sistema procurará pontos escuros arredondados. NÃO são vazadores físicos.':'O sistema tentará identificar aberturas claras dentro de uma peça mais escura. Use fundo uniforme e iluminação por baixo, quando possível.'}}</p>
        </div>
        <div class="actions">
          <label class="button secondary">Enviar fotografia<input type="file" accept="image/*" hidden @change="uploadPhoto"></label>
          <button class="button secondary" @click="cameraOn?stopCamera():startCamera()">{{cameraOn?'Desligar câmera':'Abrir webcam'}}</button>
          <button v-if="cameraOn" class="button primary" @click="photograph">Fotografar</button>
        </div>
        <video v-if="cameraOn" ref="video" autoplay muted playsinline class="video"></video>
        <div class="photo-grid">
          <div class="photo" v-if="photoUrl"><img :src="photoUrl" alt="Fotografia enviada">
            <svg v-if="preview" :viewBox="'0 0 '+preview.image_size[0]+' '+preview.image_size[1]" preserveAspectRatio="none" role="img" aria-label="Contorno vermelho e candidatos circulares em amarelo">
              <polygon :points="pointsToSvg(preview.contour)" class="photo-outline"/>
              <g v-for="point in preview.candidates" :key="point.id">
                <circle :cx="point.center[0]" :cy="point.center[1]" :r="Math.max(7, point.radius_px+4)" class="photo-point"/>
              </g>
            </svg>
          </div>
          <p v-else class="muted">Fotografe a peça com a webcam ou envie uma imagem para avaliar a extração de contorno.</p>
          <div v-if="preview" class="metrics">
            <strong>Resultado visual — {{preview.mode==='marks'?'marcas escuras':'aberturas claras'}}</strong>
            <span><b>{{preview.candidate_count}}</b> candidatos circulares encontrados na fotografia</span>
            <span><b>{{confirmedFeatures}}</b> vazadores confirmados no desenho CAD</span>
            <p v-if="preview.candidate_count!==confirmedFeatures" class="candidate-warning">As quantidades são diferentes. Isso não significa automaticamente peça defeituosa: pode ser falha de iluminação ou reconhecimento.</p>
            <p v-else class="candidate-warning">Quantidades iguais não significam posições nem dimensões corretas. Não foi feita correspondência CAD × imagem.</p>
            <p>{{preview.warnings[0]}}</p>
            <details><summary>Detalhes técnicos da segmentação</summary>
              <p>{{preview.detected_regions}} contornos brutos na imagem (texturas e ruídos incluídos).</p>
              <p v-for="point in preview.candidates" :key="point.id">{{point.id}}: centro ({{point.center.join(', ')}}) px, raio aproximado {{point.radius_px}} px.</p>
            </details>
            <p><strong>Etapa 4 — comparação em mm:</strong> ainda não disponível. Exige peça física, calibração e alinhamento geométrico.</p>
          </div>
        </div>
      </section>
      <div v-if="step===3" class="image-next-step">
        <button class="button secondary" @click="selectStep(2)">← Voltar à Etapa 2 (CAD)</button>
        <span class="note">Fim da Etapa 3 experimental. A Etapa 4 ainda não está disponível.</span>
      </div>
    </main>
    <footer>ControlVision 0.1 · Protótipo de engenharia · Nenhuma aprovação ou reprovação industrial</footer>
  </div>
</template>
