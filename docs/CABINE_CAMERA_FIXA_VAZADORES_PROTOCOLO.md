# Requisitos confirmados e protocolo de captura da cabine — ControlVision

**Data:** 04/11/2026  
**Situação:** requisitos confirmados pelo operador; **protocolo proposto, ainda não executado**.  
**Escopo:** inspeção experimental de peças cortadas em posto com câmera fixa, sem decisão automática de conformidade.

## Requisitos do processo confirmados

1. **Vazadores** são furos físicos **passantes** muito pequenos, previstos nos arquivos CAD utilizados pela máquina de corte. Pode haver falha de corte: vazador esperado ausente/incompleto, vazador deslocado, abertura extra ou recorte incorreto — estes são **cenários de investigação**, não defeitos confirmados nas fotos fornecidas.
2. **CAD disponível**: há arquivos DXF com referência das peças e posições dos vazadores/recortes. Precisaremos verificar caso a caso que essas entidades estão corretamente identificadas, com unidades e revisão do molde conhecidas.
3. **Captação prevista**: uma câmera **fixa em cabine com muita iluminação**. O produto será web e usado em vários computadores da produção. O modelo de IA pode operar em servidor, sem instalar pesos nos postos.
4. A peça pode ter diferentes cores e tramas; malhas naturais apresentam aberturas ópticas que **não equivalem aos vazadores de corte**.

## Hipótese óptica que precisa de ensaio

Iluminação forte por si só não garante que os vazadores passantes sejam distinguíveis da trama.

Comparar, **com a mesma peça física, mesma câmera/distância/foco/exposição e sem mudar o CAD**:
- **Luz frontal/difusa:** favorece contorno, detalhes superficiais, textura e alguns recortes.
- **Contraluz controlada** (luz por trás da peça): pode realçar furos passantes, mas **também ilumina aberturas normais da malha**, podendo aumentar falsos candidatos.
- **Duas capturas complementares**, se necessário: uma para silhueta e outra para perfurações. Exige sincronização e posição fixa da peça. A escolha só pode ser feita após testes.

Evitar saturação (brancos estourados), reflexos, sombras fortes e variação de exposição; capturar originais sem overlays ou filtros irreversíveis. Testar materiais claros/escuros e texturas distintas. Registrar distância da câmera, lente, resolução, exposição, iluminação e posicionamento no ambiente **privado**.

## Primeiro ensaio prático controlado (P0)

1. Selecionar **uma peça de lingueta física** e seu DXF correspondente, incluindo modelo, revisão, numeração conhecida (se disponível) e mapa de vazadores/recortes confirmados por pessoa responsável.
2. Identificar no CAD **cada vazador passante esperado** e recorte, sem inferir que todo círculo CAD seja vazador.
3. Inspecionar fisicamente a peça: para cada região CAD, anotar `presente`, `ausente/incompleto`, `posição duvidosa` ou `não observável`; documentar também **furos extras suspeitos**. A referência física não deve ser obtida apenas pela predição do algoritmo.
4. Fotografar a **mesma peça sem movimentá-la** sob luz frontal e contraluz quando seguro e viável. Se não houver contraluz disponível, registrar a limitação e realizar primeiro com luz existente; não adquirir equipamento antes de resultado exploratório.
5. Conferir visualmente no original se os menores vazadores são **distinguíveis** da trama. Testar um alvo/padrão dimensional físico conhecido para calcular a resolução efetiva da imagem; não calcular tamanho em mm a partir de imagem sem calibração.
6. Salvar dados somente em repositório/armazenamento privado autorizado, com ID de peça, lote, captura, câmera, configuração, revisão CAD e anotações revisadas.
7. **Não publicar imagens, CADs proprietários nem crops no GitHub público.** Somente código, testes sintéticos, esquema e métricas agregadas sem identificação.

## Proposta de rótulos mínimos

- `peca_mascara` (corpo externo)
- `vazador_esperado_presente` (fisicamente confirmado)
- `vazador_esperado_ausente_ou_incompleto` (fisicamente confirmado)
- `abertura_extra_suspeita` (requer revisão)
- `recorte_cad` (geometria interna/na borda)
- `trama_normal` (padrão da malha)
- `artefato_de_imagem` (sombra, reflexo, ruído, desfoco)
- `inconclusivo` (não observável ou sem revisão física)

Para treinar detecção supervisionada, rótulos de defeito precisam vir de **inspeção física revisada**, não apenas de comparação com a posição esperada. Guardar `cad_feature_id` e origem da anotação; preservar dúvidas e divergências.

## Estratégia de software após P0

1. Segmentar peça e estimar orientação com revisão humana.
2. Produzir ranking de referências CAD, incluindo **desconhecida/ambígua** quando tamanhos próximos não são separáveis. Só associar à referência quando evidência suficiente; não inferir dimensão real de escala de visualização.
3. Projetar **regiões de interesse (ROIs) CAD** sobre foto apenas após registro plausível; analisar pixels originais em resolução preservada, com recortes de tamanho ajustado à escala visual observada.
4. Fazer **busca global paralela** por aberturas extras e defeitos fora dos centros esperados (não deixar o CAD cegar o detector).
5. Investigar duas famílias de métodos: segmentação supervisionada de pequenos sinais e detecção de anomalia por textura (Anomalib, PatchCore/EfficientAD). SAM 2 continua candidato para máscara/rotulagem, não detector industrial validado de furos.
6. Avaliar separadamente por material/trama, orientação, dimensão em pixels, luz, peça física e versão CAD: recall por vazador confirmado, falsos alarmes por peça, erros na identificação CAD, taxa de inconclusivos, latência.
7. Operar IA em worker/serviço de inferência separado da API web, com controle de acesso, fila e versionamento de modelos, após provas de viabilidade.

## Critérios para seguir para treinamento

- [ ] Confirmar visibilidade dos menores vazadores com a câmera e iluminação reais.
- [ ] Ter ao menos um par foto original + CAD correspondente, **privados e revisados**.
- [ ] Comparar capturas frontal/contraluz sem presumir a melhor.
- [ ] Definir mecanismo privado de anotação e divisão por **peça física** (nunca dividir rotações da mesma peça entre treino e teste).
- [ ] Registrar baselines e erros reais antes de escolher modelo para ajuste fino.
- [ ] Validar requisitos de segurança e execução em servidor para vários postos.

**Estado atual:** requisitos esclarecidos; P0 e treinamento **não executados**; nenhuma foto publicada; sem calibração, tolerância industrial ou liberação de produção.

**Documentos relacionados:** [pesquisa de IA](PESQUISA_IA_INSPECAO_TRAMAS_CAD_2026-11-04.md), [arquitetura de IA](ARQUITETURA_IA_SOB_DEMANDA.md), [plano mestre](../PLANO_DESENVOLVIMENTO.md).


## Estado da cabine confirmado em 04/11/2026

A cabine fisica ja existe, mas a camera ainda nao foi instalada nem escolhida. A escolha do dispositivo sera feita em fase posterior, apos levantar os requisitos de resolucao, iluminacao, estabilidade e repetibilidade. Os ensaios anteriores foram feitos com fotografias exploratorias e nao validam a captura final na cabine.

O resultado historico da lingueta, incluindo a segmentacao OpenCV e os candidatos confundidos com a trama, esta em `docs/EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md`. Os ensaios com luz frontal e contraluz seguem propostos, nao executados na cabine.
