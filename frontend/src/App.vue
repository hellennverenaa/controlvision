<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

type Feature = { id: string; points: number[][]; center: number[]; shape: 'circular'|'recorte'; suggestion: string; classification: 'pendente'|'vazador'|'referencia'|'ignorar' }
type Piece = { id: string; name: string; size: string|null; points: number[][]; features: Feature[]; bbox: number[]; area_mm2: number }
type Catalog = { filename: string; format: string; units: string; count: number; pieces: Piece[]; warnings: string[] }
type PhotoCandidate = { id: string; center: number[]; radius_px: number; circularity: number; kind: string }
type MicroSignal = { id: string; center: number[]; radius_px: number; signal_levels: number; kind: string; method: string }
type ManualMark = { id: string; x: number; y: number }
type ManualRegion = {
  id: string; position_px: number[]; edge_distance_px: number
  status: 'contraste_local'|'inconclusivo'
  gray_contrast: number|null; saturation_contrast: number|null
  nearby_signal: { position_px: number[]; offset_px: number; optical_signal_levels: number; status: string } | null
  evidence: string
}
type AnnotationItem = { mark_id: string; nearest_candidate_id: string|null; nearest_distance_px: number|null; associated_candidate_id: string|null; associated_candidate_type: string|null; associated_distance_px: number|null; status: string }
type AnnotationComparison = { association_radius_px: number; manually_marked: number; nearby_associations: number; without_nearby_candidate: number; unassociated_candidates: number; marks: AnnotationItem[] }
type ManualReport = { status: 'manual_guided_preview'; results: ManualRegion[]; annotation_comparison?: AnnotationComparison; warnings: string[] }
type MatchedPoint = { cad_id: string; image_id: string; expected_px: number[]; detected_px: number[] }
type MatchPreview = { status: 'preview_only'; fit_quality: string; shape_error_relative: number; visual_shape_difference_percent: number|null; projected_contour: number[][]; matched: MatchedPoint[]; unmatched_cad: {cad_id:string;position_px:number[]}[]; unmatched_image: {image_id:string;position_px:number[]}[]; warnings: string[] }
type GuidedRegion = { cad_id: string; position_px: number[]; roi_radius_px: number;
  status: 'sinal_suspeito'|'textura_ambigua'|'inconclusivo'; optical_peaks: number;
  best_signal_px: number[]|null; best_signal_levels: number|null;
  distance_to_projected_center_px: number|null; message: string;
  max_local_signal_levels?: number|null; threshold_levels?: number|null;
  noise_sigma_levels?: number|null }
type FamilyProfile = { piece_id: string; size: string; cad_circle_count: number; fit_quality: string;
  shape_error_relative: number; nearby_candidates: number; projected_contour: number[][]; visual_shape_difference_percent: number|null;
  projected_circles: { cad_id: string; nearest_candidate_id: string|null; position_px: number[] }[];
  guided_regions?: GuidedRegion[] }
type FamilyMatching = { status: string; tested_references: number; profiles: FamilyProfile[]; warnings: string[] }
type Preview = { status: string; contour: number[][]; image_size: number[]; detected_regions: number; mode: 'marks'|'holes'; candidates: PhotoCandidate[]; candidate_count: number; micro_candidates?: MicroSignal[]; micro_candidate_count?: number; micro_signal_quality?: string; micro_signals_per_10000_px2?: number; warnings: string[]; matching?: MatchPreview|null; family_matching?: FamilyMatching|null }

const catalog = ref<Catalog|null>(null)
const selectedId = ref<string|null>(null)
const unknownSize = ref(false)
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
const pieceTone = ref<'dark'|'light'>('dark')
const lastPhoto = ref<File|null>(null)
const showMatching = ref(true)
const showFamilyPattern = ref(true)
const familyProfileIndex = ref(0)
const selectedFamilyProfile = computed(() =>
  preview.value?.family_matching?.profiles[familyProfileIndex.value] ?? null
)
const showNoisyMicro = ref(false)
const showCircleCandidates = ref(true)
const zoomPhoto = ref(false)
const annotatePhoto = ref(false)
const manualMarks = ref<ManualMark[]>([])
/** Distância entre marcações humanas e centros CAD apenas para auditar
 *  o alinhamento da prévia. Uma associação nunca confirma vazador. */
const cadVsManual = computed(() => {
  const centers = selectedFamilyProfile.value?.projected_circles
  const marks = manualMarks.value
  if (!centers || marks.length!==3 || centers.length!==3) return null
  const permutations = [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]]
  const options=permutations.map(mapping => ({
    cost: mapping.reduce((total, ci, mi) => total+
      Math.hypot(marks[mi].x-centers[ci].position_px[0],
                 marks[mi].y-centers[ci].position_px[1]),0),
    mapping,
  }))
  const best=options.reduce((x,y)=>y.cost<x.cost?y:x)
  const detected=[
    ...(preview.value?.candidates ?? []),
    ...(preview.value?.micro_candidates ?? []),
  ]
  const pairs=best.mapping.map((ci,mi)=>{
    const cadId=centers[ci].cad_id
    const guided=selectedFamilyProfile.value?.guided_regions?.find(r=>r.cad_id===cadId)
    const distance=Math.hypot(
      marks[mi].x-centers[ci].position_px[0],
      marks[mi].y-centers[ci].position_px[1],
    )
    const nearest=detected.map(candidate=>({
      id:candidate.id,
      distance:Math.hypot(marks[mi].x-candidate.center[0],marks[mi].y-candidate.center[1]),
    })).sort((x,y)=>x.distance-y.distance)[0] ?? null
    const outside=guided && distance>guided.roi_radius_px
    const belowThreshold=guided?.optical_peaks===0 &&
      guided?.max_local_signal_levels!=null && guided?.threshold_levels!=null &&
      guided.max_local_signal_levels < guided.threshold_levels
    let reason='Comparar o sinal na foto, o centro CAD e a região de busca.'
    if(outside) reason='O centro CAD projetado está fora da região que abrange o ponto marcado: revisar alinhamento ou referência.'
    else if(belowThreshold) reason='O ponto marcado está dentro da região CAD, mas o contraste não superou o filtro local.'
    return {
      mark_id:marks[mi].id,
      cad_id:cadId,
      distance_px:Math.round(distance*10)/10,
      roi_radius_px:guided?.roi_radius_px ?? null,
      nearest_photo_candidate_id:nearest?.id ?? null,
      nearest_photo_distance_px:nearest?Math.round(nearest.distance*10)/10:null,
      nearby_photo_candidate:!!nearest && nearest.distance<=12,
      diagnosis:reason,
      outside_roi:!!outside,
      below_threshold:!outside && !!belowThreshold,
    }
  })
  return {
    pairs,
    maximum_px:Math.max(...pairs.map(p=>p.distance_px)),
    outside_roi:pairs.filter(p=>p.outside_roi).length,
    nearby_photo:pairs.filter(p=>p.nearby_photo_candidate).length,
    inside_below_threshold:pairs.filter(p=>p.below_threshold).length,
  }
})
const manualReport = ref<ManualReport|null>(null)
const manualBusy = ref(false)
async function evaluateManualMarks(): Promise<void> {
  if (!lastPhoto.value || !manualMarks.value.length || manualBusy.value || photoMode.value!=='holes') return
  manualBusy.value=true;manualReport.value=null;error.value=''
  try {
    const form = new FormData()
    form.append('file',lastPhoto.value)
    form.append('marks_json',JSON.stringify(manualMarks.value))
    form.append('piece_tone',pieceTone.value)
    const response=await fetch('/api/vision/manual-regions',{method:'POST',body:form})
    const data=await response.json()
    if(!response.ok)throw new Error(data.detail??'Falha ao analisar as regiões marcadas.')
    manualReport.value=data as ManualReport
  } catch(e) {error.value=e instanceof Error?e.message:'Erro inesperado'}
  finally{manualBusy.value=false}
}
function markPhoto(event: MouseEvent): void {
  if (!annotatePhoto.value || !preview.value) return
  manualReport.value=null
  const svg = event.currentTarget as SVGSVGElement
  const matrix = svg.getScreenCTM()
  if (!matrix) return
  const p = svg.createSVGPoint()
  p.x = event.clientX
  p.y = event.clientY
  const pos = p.matrixTransform(matrix.inverse())
  const [w, h] = preview.value.image_size
  if (pos.x < 0 || pos.y < 0 || pos.x >= w || pos.y >= h) return
  manualMarks.value.push({
    id: 'M' + String(manualMarks.value.length + 1).padStart(2, '0'),
    x: Math.round(pos.x * 10) / 10,
    y: Math.round(pos.y * 10) / 10,
  })
}
function selectStep(value: 1|2|3): void {
  if (value===2 && !catalog.value) return
  if (value===3 && !selected.value && !(unknownSize.value && !!catalog.value?.pieces.length)) return
  step.value=value
  window.scrollTo({top:0,behavior:'smooth'})
}
let stream: MediaStream|null = null

const filtered = computed(() => (catalog.value?.pieces ?? []).filter(p =>
  (p.name + ' ' + p.id + ' ' + (p.size ?? '')).toLowerCase().includes(search.value.toLowerCase())
))
const selected = computed(() => unknownSize.value ? null : catalog.value?.pieces.find(p => p.id === selectedId.value) ?? null)
const canAdvance = computed(() => !!selected.value || (unknownSize.value && !!catalog.value?.pieces.length))
function selectPiece(piece: Piece): void { unknownSize.value=false; selectedId.value=piece.id }
function selectUnknownSize(): void {
  unknownSize.value=true
  selectedId.value=null
  preview.value=null;lastPhoto.value=null;manualMarks.value=[]
  if(photoUrl.value) URL.revokeObjectURL(photoUrl.value)
  photoUrl.value=''
  manualMarks.value=[];manualReport.value=null
}
const pendingFeatures = computed(() => selected.value?.features.filter(f => f.classification === 'pendente').length ?? 0)
const confirmedFeatures = computed(() => selected.value?.features.filter(f => f.classification === 'vazador').length ?? 0)
const suggestedHoles = computed(() => selected.value?.features.filter(f => f.shape === 'circular').length ?? 0)
const commonCadCircleCount = computed<number|null>(() => {
  const pieces=catalog.value?.pieces ?? []
  if(!pieces.length) return null
  const counts=pieces.map(piece=>piece.features.filter(feature=>feature.shape==='circular').length)
  return counts[0]>0 && counts.every(count=>count===counts[0]) ? counts[0] : null
})
const excessiveCircleCandidates = computed(() => {
  const expected=commonCadCircleCount.value
  if(!preview.value || !expected || preview.value.mode!=='holes') return false
  return preview.value.candidate_count>=Math.max(10,expected*3)
})
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
    selectedId.value=catalog.value.pieces.length===1 ? catalog.value.pieces[0].id : null
    unknownSize.value=catalog.value.pieces.length>1
    photoMode.value='holes'
    highlightedFeatureId.value=null
    step.value=catalog.value.pieces.length?2:1
  } catch (e) { error.value=e instanceof Error?e.message:'Erro inesperado' }
  finally { busy.value=false }
}

async function processPhoto(file: File): Promise<void> {
  if (lastPhoto.value !== file) manualMarks.value=[]
  manualReport.value=null
  lastPhoto.value=file
  showNoisyMicro.value=false
  familyProfileIndex.value=0
  preview.value=null;error.value='';busy.value=true
  if(photoUrl.value) URL.revokeObjectURL(photoUrl.value)
  photoUrl.value=URL.createObjectURL(file)
  try {
    const form=new FormData();form.append('file',file);form.append('mode',photoMode.value);form.append('piece_tone',pieceTone.value)
    if (unknownSize.value && catalog.value?.pieces.length) form.append('cad_family_data',
      JSON.stringify(catalog.value.pieces.map(piece=>({
        id:piece.id,name:piece.name,size:piece.size,
        points:piece.points,
        features:piece.features.filter(feature=>feature.shape==='circular')
          .map(feature=>({id:feature.id,center:feature.center,shape:feature.shape}))
      })))
    )
    if (selected.value) form.append('cad_data', JSON.stringify({
      contour: selected.value.points,
      features: selected.value.features.filter(feature=>feature.classification==='vazador')
        .map(feature=>({id:feature.id,center:feature.center,classification:feature.classification}))
    }))
    const response=await fetch('/api/vision/preview',{method:'POST',body:form})
    const result=await response.json()
    if (!response.ok) throw Error(result.detail ?? 'Falha ao analisar imagem.')
    preview.value=result as Preview
    const expected=commonCadCircleCount.value
    showCircleCandidates.value=!(photoMode.value==='holes' && expected &&
      result.candidate_count>=Math.max(10,expected*3))
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
    stream=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:1920},height:{ideal:1080},frameRate:{ideal:15}},audio:false})
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
watch([photoMode,pieceTone], () => { manualReport.value=null; if(lastPhoto.value) void processPhoto(lastPhoto.value) })
watch(selectedId, () => {preview.value=null;lastPhoto.value=null;manualMarks.value=[];manualReport.value=null;if(photoUrl.value)URL.revokeObjectURL(photoUrl.value);photoUrl.value='' })
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
        <button type="button" :disabled="!canAdvance" :class="['workflow-step',step===3?'current':'',preview?'done':'']" :aria-current="step===3?'step':undefined" @click="selectStep(3)"><span>3</span><strong>Analisar fotografia</strong><small>Pontos e aberturas</small></button>
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
            <button v-if="(catalog?.pieces.length ?? 0)>1" :class="['item','unknown-option',unknownSize?'active':'']" @click="selectUnknownSize">
              <span class="piece-id">?</span><span><strong>Não sei a numeração</strong><small>Experimentar sem escolher um tamanho</small></span><b>›</b>
            </button>
            <button v-for="piece in filtered" :key="piece.id" :class="['item',selectedId===piece.id && !unknownSize?'active':'']" @click="selectPiece(piece)">
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
                    <polygon :points="pointsToSvg(piece.points)" :class="['shape',selectedId===piece.id?'selected':'']" @click="selectPiece(piece)"/>
                    <g v-for="feature in piece.features" :key="feature.id" @click="selectPiece(piece)">
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
            <div v-if="unknownSize" class="review-banner"><strong>Numeração desconhecida</strong><span>O arquivo contém {{catalog?.pieces.length}} moldes. Selecione um para revisar vazadores ou avance para testar só a foto.</span></div>
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
      <div v-if="step===2 && canAdvance" class="next-step">
        <div><strong>Próximo passo: testar uma fotografia {{unknownSize?'sem numeração definida':'do molde selecionado'}}</strong>
        <p>Sem saber a numeração, o teste mostrará apenas os contornos da foto, sem comparar com um tamanho escolhido ao acaso. Não precisa de régua agora.</p></div>
        <button class="button primary" @click="goToPhoto">Continuar para Etapa 3 →</button>
      </div>
      <section v-if="step===3" class="panel camera" id="etapa-foto">
        <div class="panel-title"><div><span class="eyebrow">ETAPA 3 · IMAGEM EXPERIMENTAL</span><h2>Visualizar o contorno detectado na fotografia</h2></div><span class="tag small">PIXELS — SEM COMPARAÇÃO</span></div>
        <div class="image-guide">
          <template v-if="selected"><strong>Molde CAD: {{selected.name}}</strong> · {{confirmedFeatures}} vazadores confirmados.</template>
          <template v-else><strong>Numeração desconhecida</strong> · {{catalog?.pieces.length}} moldes disponíveis, nenhum escolhido para comparação.</template>
          <br>Contorno vermelho = fotografia. Círculos amarelos = candidatos visuais, não inspeção dimensional.</div>
        <div class="photo-controls">
          <strong>O que está sendo fotografado?</strong>
          <label><input v-model="photoMode" type="radio" value="marks"> Desenho no papel com pontos escuros</label>
          <label><input v-model="photoMode" type="radio" value="holes"> Peça física cortada (furos)</label>
          <div v-if="photoMode==='holes'" class="tone-selector">
            <strong>Contraste entre peça e fundo:</strong>
            <label><input v-model="pieceTone" type="radio" value="dark"> Peça escura, fundo claro</label>
            <label><input v-model="pieceTone" type="radio" value="light"> Peça clara, fundo mais escuro</label>
          </div>
          <p class="note">{{photoMode==='marks'?'Pontos desenhados não são furos físicos.':'Selecione o tom da peça em relação ao fundo. Capturas com contraste insuficiente devem ser consideradas inconclusivas. Para furos minúsculos, aproxime a câmera sem cortar a peça da imagem e evite desfoque; uma foto de baixa resolução pode não resolvê-los.'}}</p>
        </div>
        <div class="actions">
          <label class="button secondary">Enviar fotografia<input type="file" accept="image/*" hidden @change="uploadPhoto"></label>
          <button class="button secondary" @click="cameraOn?stopCamera():startCamera()">{{cameraOn?'Desligar câmera':'Abrir webcam'}}</button>
          <button v-if="cameraOn" class="button primary" @click="photograph">Fotografar</button>
        </div>
        <video v-if="cameraOn" ref="video" autoplay muted playsinline class="video"></video>
        <div v-if="photoUrl && preview" class="photo-review-controls">
          <button class="button secondary" type="button" @click="zoomPhoto=!zoomPhoto">
            {{zoomPhoto?'Reduzir fotografia':'Ampliar fotografia'}}
          </button>
          <button class="button secondary" type="button" :aria-pressed="annotatePhoto" @click="annotatePhoto=!annotatePhoto">
            {{annotatePhoto?'Encerrar marcação manual':'Marcar furinhos manualmente'}}
          </button>
          <button v-if="manualMarks.length" class="button secondary" type="button" @click="manualMarks.pop();manualReport=null">Desfazer último ponto</button>
          <button v-if="manualMarks.length" class="button secondary" type="button" @click="manualMarks=[];manualReport=null">Limpar marcações</button>
          <button v-if="manualMarks.length && photoMode==='holes'" class="button primary" type="button" :disabled="manualBusy"
            @click="evaluateManualMarks">{{manualBusy?'Analisando…':'Analisar regiões marcadas'}}</button>
          <p class="note">Ampliação não cria detalhes na imagem. Os pontos roxos são anotações humanas. A análise procura contraste apenas ao redor desses pontos e <strong>não é detecção automática nem confirmação de furo.</strong></p>
          <section v-if="manualReport" class="manual-results" aria-label="Resultados da análise assistida">
            <strong>Análise assistida por marcações — pixels, sem conclusão dimensional</strong>
            <p class="note">Pontos com contraste podem ser furos, sombras ou textura. Pontos inconclusivos não significam furos ausentes.</p>
            <section v-if="manualReport.annotation_comparison" class="annotation-compare">
              <strong>Marcadores humanos × candidatos automáticos (proximidade visual)</strong>
              <p>{{manualReport.annotation_comparison.nearby_associations}} de {{manualReport.annotation_comparison.manually_marked}}
                marcações com candidato próximo (até {{manualReport.annotation_comparison.association_radius_px}} px).</p>
              <p>{{manualReport.annotation_comparison.unassociated_candidates}} candidatos sem correspondência
                com os pontos marcados. Isso não determina quais são furos.</p>
              <div v-for="comparison in manualReport.annotation_comparison.marks" :key="comparison.mark_id" class="annotation-row">
                <strong>{{comparison.mark_id}}</strong>
                <span v-if="comparison.associated_candidate_id">
                  Próximo: {{comparison.associated_candidate_id}}
                  ({{comparison.associated_candidate_type}}) a {{comparison.associated_distance_px}} px.
                </span>
                <span v-else>
                  Sem candidato próximo.
                  <template v-if="comparison.nearest_candidate_id">
                    O mais próximo é {{comparison.nearest_candidate_id}} a {{comparison.nearest_distance_px}} px.
                  </template>
                </span>
              </div>
              <p class="note">Raio de proximidade não é tolerância dimensional nem confirmação de um vazador físico.</p>
            </section>
            <div v-for="point in manualReport.results" :key="point.id" class="manual-result">
              <span>{{point.id}} · {{point.status==='contraste_local'?'Contraste observado':'Inconclusivo'}}</span>
              <span>{{point.evidence}}</span>
              <small>Distância da borda: {{point.edge_distance_px}} px · Contraste no clique: {{point.gray_contrast===null?'—':point.gray_contrast+' níveis'}}</small>
              <small v-if="point.nearby_signal" class="nearby-indication">
                Sinal óptico próximo: {{point.nearby_signal.optical_signal_levels}} níveis, deslocamento {{point.nearby_signal.offset_px}} px do clique.
                Localização sugerida ({{point.nearby_signal.position_px.join(', ')}}) px. <strong>Não é furo confirmado.</strong>
              </small>
              <small v-else>Nenhum sinal escuro suficientemente destacado na vizinhança do clique.</small>
            </div>
          </section>
        </div>
        <div :class="['photo-grid',zoomPhoto?'with-zoom':'']">
          <div :class="['photo',zoomPhoto?'inspection-zoom':'']" v-if="photoUrl"><img :src="photoUrl" alt="Fotografia enviada">
            <svg v-if="preview && preview.status!=='capture_invalid'" :viewBox="'0 0 '+preview.image_size[0]+' '+preview.image_size[1]" preserveAspectRatio="none"
              role="img" aria-label="Contorno vermelho da foto, candidatos amarelos e sobreposição CAD azul ilustrativa">
              <polygon :points="pointsToSvg(preview.contour)" class="photo-outline"/>
              <g v-if="showCircleCandidates" v-for="point in preview.candidates" :key="point.id">
                <circle :cx="point.center[0]" :cy="point.center[1]" :r="Math.max(7, point.radius_px+4)" class="photo-point">
                  <title>{{point.id}} · candidato circular clássico na fotografia</title>
                </circle>
              </g>
              <g v-for="spot in (preview.micro_signal_quality==='excesso_de_textura' && !showNoisyMicro ? [] : (preview.micro_candidates ?? []))" :key="spot.id">
                <circle :cx="spot.center[0]" :cy="spot.center[1]" :r="Math.max(8, spot.radius_px+5)" class="photo-micro-signal">
                  <title>{{spot.id}} · pequeno sinal óptico automático, {{spot.signal_levels}} níveis. NÃO é furo confirmado.</title>
                </circle>
              </g>
              <g v-if="showFamilyPattern && selectedFamilyProfile && selectedFamilyProfile.fit_quality!=='baixa'"
                class="family-projected-points">
                <polygon :points="pointsToSvg(selectedFamilyProfile.projected_contour)"
                  class="cad-illustrative-outline">
                  <title>Contorno azul tracejado: projeção ilustrativa CAD, não medida dimensional.</title>
                </polygon>
                <g v-for="expected in selectedFamilyProfile.projected_circles" :key="expected.cad_id">
                  <circle :cx="expected.position_px[0]" :cy="expected.position_px[1]" r="12"
                    class="family-expected-ring">
                    <title>{{expected.cad_id}}: projeção ilustrativa do molde {{selectedFamilyProfile.size}}. Não é medida.</title>
                  </circle>
                  <circle :cx="expected.position_px[0]" :cy="expected.position_px[1]" r="2" class="family-expected-center"/>
                </g>
              </g>
              <g v-if="showMatching && preview.matching" class="match-overlay">
                <polygon :points="pointsToSvg(preview.matching.projected_contour)" class="cad-illustrative-outline"/>
                <g v-for="match in preview.matching.matched" :key="match.cad_id">
                  <line :x1="match.expected_px[0]" :y1="match.expected_px[1]" :x2="match.detected_px[0]" :y2="match.detected_px[1]" class="match-link"/>
                  <circle :cx="match.expected_px[0]" :cy="match.expected_px[1]" r="6" class="cad-match-point">
                    <title>{{match.cad_id}} → {{match.image_id}} (associação visual)</title>
                  </circle>
                </g>
                <g v-for="point in preview.matching.unmatched_cad" :key="point.cad_id">
                  <circle :cx="point.position_px[0]" :cy="point.position_px[1]" r="7" class="cad-unmatched-point">
                    <title>{{point.cad_id}} · sem candidato associado (não confirma ausência física)</title>
                  </circle>
                </g>
              </g>
            </svg>
            <svg v-if="preview" :viewBox="'0 0 '+preview.image_size[0]+' '+preview.image_size[1]"
              preserveAspectRatio="none" :class="['manual-overlay',annotatePhoto?'mark-active':'']"
              role="img" aria-label="Marcadores manuais roxos posicionados pelo operador"
              @click="markPhoto">
              <g v-for="mark in manualMarks" :key="mark.id" class="manual-mark">
                <circle :cx="mark.x" :cy="mark.y" r="8"/>
                <line :x1="mark.x-14" :y1="mark.y" :x2="mark.x+14" :y2="mark.y"/>
                <line :x1="mark.x" :y1="mark.y-14" :x2="mark.x" :y2="mark.y+14"/>
                <title>{{mark.id}}: marcação manual, não vazador confirmado</title>
              </g>
            </svg>
          </div>
          <p v-else class="muted">Fotografe a peça com a webcam ou envie uma imagem para avaliar a extração de contorno.</p>
          <div v-if="preview?.status==='capture_invalid'" class="metrics">
            <strong class="capture-invalid">Captura inconclusiva</strong>
            <p>Não foi possível isolar a peça do fundo com confiança. Nenhum vazador foi identificado ou comparado ao CAD.</p>
            <p>{{preview.warnings[0]}}</p>
            <p>Tente outro fundo ou mude o contraste selecionado. Não é necessário medir a peça para repetir.</p>
          </div>
          <div v-else-if="preview" class="metrics">
            <strong>Resultado visual — {{preview.mode==='marks'?'marcas escuras':'aberturas claras'}}</strong>
            <p v-if="preview.mode==='holes' && preview.image_size[0]*preview.image_size[1]<500000" class="resolution-warning">
              Imagem reduzida ({{preview.image_size[0]}} × {{preview.image_size[1]}} px): pequenos vazadores podem perder detalhes e não ser detectados. Use a captura original em maior resolução para testar micropontos.
            </p>
            <span><b>{{preview.candidate_count}}</b> candidatos circulares clássicos (amarelo)</span>
            <div v-if="excessiveCircleCandidates" class="micro-noise-alert">
              <strong>Quantidade excessiva de candidatos circulares: conferir textura.</strong>
              <p>Os moldes do CAD possuem {{commonCadCircleCount}} geometrias circulares internas cada,
                mas a fotografia gerou {{preview.candidate_count}} candidatos.
                Esse excesso pode incluir a trama do material; não indica quantidade de furos presentes.</p>
              <label><input v-model="showCircleCandidates" type="checkbox">
                Mostrar os {{preview.candidate_count}} candidatos amarelos para diagnóstico
              </label>
            </div>
            <div v-if="preview.micro_signal_quality==='excesso_de_textura'" class="micro-noise-alert">
              <strong>Detecção instável: excesso de sinais compatível com textura do material.</strong>
              <p>O detector encontrou {{preview.micro_candidate_count}} micropontos, mas a contagem não é confiável para identificar vazadores. Não interprete esse número como quantidade de furos.</p>
              <label><input v-model="showNoisyMicro" type="checkbox"> Mostrar os sinais cianos para análise técnica</label>
            </div>
            <template v-else>
              <span><b>{{preview.micro_candidate_count ?? 0}}</b> micropontos de contraste sugeridos automaticamente (ciano, não confirmados)</span>
              <p v-if="(preview.micro_candidate_count ?? 0)>0" class="micro-warning">
                Micropontos encontrados automaticamente por contraste local. Podem ser furos, sujeira ou trama. Não entram na correspondência CAD nem indicam conformidade.
              </p>
            </template>
            <span><b>{{manualMarks.length}}</b> pontos marcados manualmente (não entram no algoritmo)</span>
            <details v-if="manualMarks.length"><summary>Coordenadas das marcações manuais</summary>
              <p v-for="mark in manualMarks" :key="mark.id">{{mark.id}}: ({{mark.x}}, {{mark.y}}) px — anotação visual, não medição</p>
            </details>
            <span v-if="selected"><b>{{confirmedFeatures}}</b> vazadores confirmados no CAD</span>
            <span v-else>Numeração desconhecida — nenhum tamanho foi escolhido. A foto não permite inferir medidas reais.</span>
            <p v-if="photoMode==='holes' && preview.candidate_count===0 && !(preview.micro_candidate_count ?? 0)" class="candidate-warning">
              Nenhum candidato óptico detectado automaticamente. Furos minúsculos podem ser invisíveis nesta resolução; isso NÃO comprova ausência.
            </p>
            <p v-else-if="photoMode==='holes'" class="note">Os pontos amarelos e cianos são apenas candidatos ópticos, não vazadores confirmados. A fotografia atual ainda não serve para liberar peças.</p>
            <div v-if="preview.family_matching" class="match-report family-preview">
              <strong>Prévia do padrão CAD × foto — sem identificação de numeração</strong>
              <p>{{preview.family_matching.tested_references}} referências avaliadas.
                Todas utilizam escala de exibição normalizada. Nenhuma foi escolhida como tamanho real.</p>
              <p v-if="preview.family_matching.status==='contorno_inconclusivo'" class="candidate-warning">
                Nenhum contorno apresentou ajuste visual suficientemente confiável. As posições projetadas não devem ser utilizadas.
              </p>
              <template v-if="preview.family_matching.profiles.length">
                <label class="family-select">Escolher referência apenas para visualizar o padrão:
                  <select v-model.number="familyProfileIndex">
                    <option v-for="(profile, index) in preview.family_matching.profiles" :key="profile.piece_id" :value="index">
                      {{profile.size}} — ajuste {{profile.fit_quality}}, {{profile.nearby_candidates}} candidato(s) próximo(s)
                    </option>
                  </select>
                </label>
                <label class="match-toggle">
                  <input v-model="showFamilyPattern" type="checkbox"> Mostrar contorno e centros CAD em azul tracejado (apenas projeção ilustrativa)
                </label>
                <span v-if="selectedFamilyProfile"><b>{{selectedFamilyProfile.nearby_candidates}}</b> de
                  {{selectedFamilyProfile.cad_circle_count}} geometrias circulares com algum candidato próximo, nesta referência experimental.</span>
                <p v-if="selectedFamilyProfile" class="note">
                  Qualidade do ajuste do contorno: <strong>{{selectedFamilyProfile.fit_quality}}</strong>.
                  Compare primeiro o azul tracejado com a borda vermelha. Só depois interprete os centros azuis.
                  Um alinhamento aparentemente bom não comprova vazadores nem dimensões.
                </p>
                <p v-if="selectedFamilyProfile?.visual_shape_difference_percent != null" class="note">
                  Área de divergência das silhuetas sobrepostas:
                  <strong>{{selectedFamilyProfile.visual_shape_difference_percent.toFixed(1)}}%</strong>
                  (escala normalizada só para visualização; NÃO é percentual de erro dimensional da peça).
                </p>
                <p v-if="selectedFamilyProfile?.guided_regions?.length" class="note">
                  Análise guiada pelo CAD: examina contraste em regiões pequenas próximas dos centros azuis;
                  NÃO detecta nem confirma furos automaticamente. A detecção global continua independente.
                </p>
                <div v-if="selectedFamilyProfile?.guided_regions?.length" class="guided-results">
                  <strong>Investigação óptica dos {{selectedFamilyProfile.guided_regions.length}} centros previstos — não metrológica</strong>
                  <div v-for="region in selectedFamilyProfile.guided_regions" :key="region.cad_id" class="guided-region">
                    <b>{{region.cad_id}} · {{region.status==='textura_ambigua'?'Textura ambígua':region.status==='sinal_suspeito'?'Sinal suspeito':'Inconclusivo'}}</b>
                    <span>{{region.message}}</span>
                    <small>Raio da região: {{region.roi_radius_px}} px · picos acima do limiar: {{region.optical_peaks}}.
                      <template v-if="region.max_local_signal_levels!==null && region.max_local_signal_levels!==undefined">
                        Máximo observado: {{region.max_local_signal_levels}} níveis ·
                        limiar exigido: {{region.threshold_levels}} níveis ·
                        ruído local estimado: {{region.noise_sigma_levels}}.
                      </template>
                      <template v-if="region.best_signal_px"> · pico selecionado: {{region.best_signal_levels}} níveis,
                        a {{region.distance_to_projected_center_px}} px do centro projetado</template>
                    </small>
                  </div>
                  <div v-if="cadVsManual" class="manual-cad-review">
                    <strong>Conferência humana: alinhamento CAD × detecção óptica</strong>
                    <p>{{cadVsManual.nearby_photo}} de 3 marcações com algum candidato automático até 12 px.
                      {{cadVsManual.outside_roi}} de 3 fora da região CAD projetada.
                      {{cadVsManual.inside_below_threshold}} dentro da região, mas abaixo do limiar do filtro.</p>
                    <p>Máxima distância entre marcação humana e centro CAD: {{cadVsManual.maximum_px}} px.
                      Essas diferenças NÃO são erros dimensionais da peça.</p>
                    <div v-for="item in cadVsManual.pairs" :key="item.mark_id" class="manual-cad-row">
                      <b>{{item.mark_id}} → {{item.cad_id}}</b>
                      <span>Centro CAD a {{item.distance_px}} px
                        <template v-if="item.roi_radius_px!==null">(região de investigação: {{item.roi_radius_px}} px)</template>.
                      </span>
                      <span v-if="item.nearest_photo_candidate_id">
                        Candidato automático mais próximo: {{item.nearest_photo_candidate_id}}
                        a {{item.nearest_photo_distance_px}} px
                        — {{item.nearby_photo_candidate?'próximo da anotação':'longe da anotação'}}.
                      </span>
                      <span v-else>Nenhum candidato automático disponível para comparação.</span>
                      <span class="manual-cad-diagnosis">{{item.diagnosis}}</span>
                    </div>
                    <p class="note">Os pontos roxos são anotações humanas. Proximidade óptica não comprova furo físico.
                      O alinhamento usa normalização visual de escala; não identifica numeração ou conformidade.</p>
                  </div>
                  <p v-else class="note">Para investigar se os centros CAD ficaram deslocados, marque os três
                    furinhos visíveis em roxo: a distância de cada clique ao centro azul será mostrada aqui.
                    Não precisa ajustar o CAD nem a sensibilidade para esse teste.</p>
                  <p class="note">Análise condicionada à posição CAD projetada. Um furo deslocado pode ficar fora dessa região;
                    portanto, a busca global e a revisão dos candidatos extras continuam necessárias.</p>
                </div>
                <p class="note">Os nove tamanhos podem ser indistinguíveis sem escala métrica. Um encaixe aparente não identifica a numeração nem confirma os furos.</p>
              </template>
            </div>
            <div v-if="preview.matching" class="match-report">
              <strong>Prévia de correspondência geométrica (sem calibração)</strong>
              <label class="match-toggle"><input v-model="showMatching" type="checkbox"> Mostrar contorno CAD projetado e pontos associados na foto</label>
              <span><b>{{preview.matching.matched.length}}</b> associações experimentais</span>
              <p v-if="preview.matching.visual_shape_difference_percent!==null" class="shape-score">
                Diferença visual dos contornos: <strong>{{preview.matching.visual_shape_difference_percent.toFixed(2)}}%</strong>
                <small>Índice experimental de área não sobreposta após normalização da escala. NÃO representa percentual de erro de corte nem conformidade.</small>
              </p>
              <p v-else class="candidate-warning">Diferença visual indisponível: sobreposição da silhueta não confiável.</p>
              <span><b>{{preview.matching.unmatched_cad.length}}</b> pontos CAD sem associação</span>
              <span><b>{{preview.matching.unmatched_image.length}}</b> candidatos extras na foto</span>
              <p :class="preview.matching.fit_quality==='baixa'?'candidate-warning':'note'">
                Qualidade do ajuste visual: {{preview.matching.fit_quality}}.
                <strong>Os pontos sem associação NÃO são defeitos confirmados.</strong>
              </p>
              <p class="note">A escala de visualização foi estimada a partir das silhuetas. Não altera o CAD original, mas também não serve para medir em milímetros.</p>
              <details><summary>Correspondências encontradas</summary>
                <p v-if="!preview.matching.matched.length">Nenhuma associação suficientemente próxima.</p>
                <p v-for="pair in preview.matching.matched" :key="pair.cad_id">{{pair.cad_id}} → {{pair.image_id}}</p>
              </details>
            </div>
            <p v-else-if="unknownSize" class="note">Foi feita somente uma prévia de padrões para as referências disponíveis; a numeração continua desconhecida e não há comparação dimensional.</p>
            <p v-else class="note">Correspondência visual indisponível; confira o contorno, a imagem e a referência selecionada.</p>
            <p v-if="preview.matching" class="candidate-warning">
              A correspondência visual foi calculada, mas nenhuma posição ou dimensão foi validada em milímetros.
              Mesmo {{preview.matching.matched.length}} associações não comprovam a presença ou a posição correta dos vazadores físicos.
            </p>
            <p v-else-if="!selected" class="candidate-warning">Os candidatos encontrados são apenas observações da fotografia. A numeração não foi identificada.</p>
            <p v-else-if="preview.candidate_count!==confirmedFeatures" class="candidate-warning">
              Quantidades diferentes podem resultar de pontos reais ausentes, ruído ou falha na detecção; não é uma reprovação.
            </p>
            <p v-else class="candidate-warning">
              As quantidades coincidem, mas ainda não foi possível estabelecer a correspondência geométrica.
            </p>
            <p>{{preview.warnings[0]}}</p>
            <details><summary>Detalhes técnicos da segmentação</summary>
              <p>{{preview.detected_regions}} contornos brutos na imagem (texturas e ruídos incluídos).</p>
              <p v-for="point in preview.candidates" :key="point.id">{{point.id}} (círculo): centro ({{point.center.join(', ')}}) px, raio aproximado {{point.radius_px}} px.</p>
              <p v-for="point in preview.micro_candidates ?? []" :key="point.id">{{point.id}} (microponto): centro ({{point.center.join(', ')}}) px, sinal {{point.signal_levels}} níveis. Não é furo confirmado.</p>
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
