# Pesquisa aplicada — IA para reconhecimento CAD e inspeção de tecidos com trama (ControlVision)

**Data:** 04/11/2026  
**Tipo:** pesquisa de projetos públicos + análise visual qualitativa de três fotografias compartilhadas pelo operador.  
**Estado:** proposta de arquitetura e validação; **nenhum modelo treinado, nenhuma métrica real obtida, nenhuma inferência executada**.  
**Referências de código externas:** projetos públicos; verificar versões, compatibilidade e licenças antes de incorporar dependências.

## 1. Problema real demonstrado

O ControlVision deve operar pela **web para vários computadores da produção**: reconhecer qual peça CAD corresponde à peça física vista pela câmera e identificar **vazadores pequenos, recortes e possíveis alterações não previstas**, com superfícies de diferentes cores, malhas, texturas e orientações.

Nas três fotografias fornecidas na conversa, observa-se uma peça branca de malha sobre fundo azul, em orientações distintas. A trama tem numerosas pequenas aberturas regulares que **não podem ser contadas automaticamente como vazadores**. Há variações locais nas bordas/superfície; uma inspeção visual isolada não confirma que sejam defeitos.

**Restrições:** as fotografias são exemplos privados; **não anexar imagens, recortes, máscaras derivadas, moldes CAD nem metadados sensíveis ao GitHub público**. Sem inspeção física ou rótulos humanos, não é possível declarar quais pontos representam furos reais. Fotografias JPEG com iluminação frontal e textura visível podem não registrar furos micrométricos com contraste/resolução suficientes. Nenhuma medição em milímetros sem calibração.

### Três tarefas distintas

1. **Segmentação do corpo da peça**: separar material do fundo, em cores/tramas variáveis.
2. **Identificação da referência CAD**: ranking sobre família/modelo e numerações com orientação/espelhamento controlados; opção obrigatória **não identificado/ambíguo**; validar geometria interna, não escolher tamanho arbitrário.
3. **Inspeção interna/localizada de alta resolução**: distinguir textura normal, vazadores CAD legítimos, recortes e anomalias fora das regiões previstas. A ausência de candidato não prova ausência física.

A geometria CAD é uma **referência estrutural** para posições e formato de vazadores/recortes. A IA complementa, mas não substitui, geometria e metrologia calibrada. Uma escala ajustada apenas para encaixar imagens jamais comprova ausência de desvio dimensional.

## 2. Pesquisa em repositórios reais e transferibilidade

| Projeto GitHub | O que implementa | Uso proposto no ControlVision | Limitação a validar |
|---|---|---|---|
| Meta SAM 2 — https://github.com/facebookresearch/sam2 | Segmentação por prompts em imagens/vídeos; código de ajuste fino e checkpoints oficiais | Baseline auxiliar e anotação de máscara externa | Não é detector especializado em microvazadores; desempenho em CPU/malha precisa ser medido; licença Apache-2.0 declarada pelo projeto |
| open-edge-platform/anomalib — https://github.com/open-edge-platform/anomalib | Métodos de detecção/localização de anomalias industriais (ex.: PatchCore, EfficientAD) | Comparar textura normal versus sinais incomuns em patches da peça | Anomalia != furo; peças de diferentes malhas podem exigir estratificação; licença Apache-2.0 no repositório |
| CVAT — https://github.com/cvat-ai/cvat | Rotulagem de imagens, máscaras, polígonos, revisão, colaboração e integração de modelos | Dataset privado anotado/revisado por operação e qualidade | Infraestrutura e fluxo de revisão necessários; licença MIT no núcleo comunitário; verificar componentes |
| Meta DINOv2 — https://github.com/facebookresearch/dinov2 | Features visuais sem treinamento supervisionado da aplicação | Experimento de recuperação por aparência/família a partir de foto | Referência CAD é desenho, não fotografia; correspondência exige estratégia multimodal/geométrica; licencia Apache-2.0 no projeto |
| Ultralytics — https://github.com/ultralytics/ultralytics | Treinamento de detecção/segmentação em dados personalizados | Baseline supervisionado de peças/recortes após dataset | Redução da imagem pode apagar furos mínimos; AGPL-3.0 na distribuição aberta; revisão jurídica antes de uso empresarial |
| BentoML — https://github.com/bentoml/BentoML | APIs, filas e hospedagem de modelos de IA | Referência para worker de inferência separado do FastAPI de negócio | Adotar depois de medir recursos, latência e volume; não implica que já esteja integrado |
| OpenVINO Model Server — https://github.com/openvinotoolkit/model_server | Serving via REST/KServe e opções de execução em CPU Intel | Alternativa a explorar se hardware/modelo forem compatíveis | Conversão e suporte por modelo exigem teste; não assumir que SAM 2 funcionará diretamente |

**Fontes complementares:** https://www.mvtec.com/research-teaching/datasets/mvtec-ad e https://www.mvtec.com/research-teaching/datasets/mvtec-ad-2 demonstram experimentos de anomalia e variabilidade industrial, **não constituem dataset de calçados**. Atenção: MVTec AD tem termos CC BY-NC-SA e **não deve ser presumido liberado para uso comercial**.

Esses repositórios são **referências de implementação**, não evidência de precisão nas nossas imagens. Não foi encontrado nem validado um modelo pronto que resolva simultaneamente identificação CAD, recortes e microvazadores em malha de calçados.

## 3. Arquitetura proposta para múltiplos postos web

```text
N postos da produção (navegador/câmera)
    -> HTTPS + autenticação + upload controlado
    -> API FastAPI (metadados, controle de trabalho, CAD, resultados)
    -> job assíncrono + fila (IDs, timeout, retry limitado, métricas)
    -> workers de IA separados (GPU/CPU, modelos versionados)
       A. segmentação corpo da peça
       B. reconhecimento/ranking da família CAD
       C. inspeção de patches/recortes/vazadores
    -> composição com CAD + validação geométrica
    -> resultado explicável: candidatos, inconclusivos, revisão humana
```

**Não enviar fotos/CAD proprietários a terceiros sem autorização.** Preferir inicialmente servidor/serviço da organização, acessível via aplicação web; não instalar pesos em cada posto. Worker pode ser hospedado na rede da empresa ou infraestrutura contratada com garantias de privacidade. Provedor e GPU ainda não definidos.

**Fallback:** se worker indisponível, retornar `indisponivel` ou `inconclusivo`, nunca dar falso veredito. Preservar OpenCV baseline e o contrato v1; estender versões explicitamente, sem modificar silenciosamente respostas antigas.

## 4. Pipeline experimental recomendado

### A. Captura

- Fotografar com câmera fixa, distância/ângulo conhecidos, luz estável, fundo contrastante; experimentar iluminação frontal e **contraluz** conforme a abertura real e material, sem pressupor que uma configuração serve para todos.
- Guardar resolução original e metadados da câmera **somente em armazenamento privado**. Não reduzir toda imagem para avaliar microvazadores.
- Definir tamanho mínimo físico do vazador e verificar quantos pixels ele ocupa no sensor; realizar ensaio com padrão físico conhecido. Sem isso, resultados de IA podem ser inconclusivos por limitação óptica.
- Rejeitar capturas com foco, brilho, perspectiva ou isolamento inadequados.

### B. Máscara da peça

- Comparar OpenCV atual, SAM 2 assistido, e modelo supervisionado de segmentação se o dataset justificar.
- Rotular máscara externa revisada manualmente; IoU/Dice e erro de borda contra ground truth; avaliar também taxa de captura inválida por material/fundo.

### C. Identificação de referência

- Primeiro gerar candidatos de **família e forma externa** usando máscara normalizada para rotação/translação, verificando espelhamento sem assumir lateralidade.
- Comparar geometrias CAD reais com silhueta e **características internas confirmadas**; tamanho/numeração só quando informação discriminar os CADs. Sem escala calibrada ou anotação confiável, manter `desconhecido` e ranking, sem atribuição automática.
- Testar DINOv2 como **auxiliar à recuperação por aparência/família**, não como comparador direto de embeddings de CAD vs foto.
- Métricas: Top-1/Top-k na família, taxa de não-identificados corretos, matriz de confusão entre numerações/espelhamentos; avaliar resultados por material e orientação.

### D. Microvazadores, recortes e trama

- Manter dois canais de investigação **independentes**:
  1. **CAD-guided:** analisar recortes de imagem de **resolução original** em torno das posições projetadas, sem concluir ausência quando projeção ou segmentação falhar. Verificar padrões de tamanho e formato diversos.
  2. **Busca global:** pesquisar candidatos fora do CAD para não perder furos deslocados/extras.
- Rotular separadamente: `trama_normal`, `vazador_confirmado`, `recorte_previsto`, `abertura_nao_prevista`, `sombra/mancha`, `incerto`. A anotação humana de localização deve ser revisada contra peça física sempre que possível.
- Comparar baseline OpenCV atual, segmentação de patches supervisionada e detecção de anomalia PatchCore/EfficientAD. Não treinar diretamente com todos os pontos escuros marcados como furos.
- Métricas: **recall por vazador físico** com correspondência espacial, precisão/alertas falsos por peça, recall estratificado por diâmetro em pixels, por malha/cor, por iluminação e por orientação; qualidade de classificação de recortes e anomalias. Não usar só contagem de círculos ou IoU geral da peça.
- Incerteza: não concluir `furo ausente` somente pela falta de sinal; manter estado `inconclusivo` para regiões não observáveis.

### E. Dataset privado auditável

- Fotos **originais** sem overlays em múltiplas rotações/distâncias/iluminações, peças com e sem vazadores e recortes **fisicamente confirmados**, várias tramas e cores.
- Anotações: contorno externo, referência CAD candidata/confirmada, localização e tipo de estrutura interna, máscara da trama e qualidade de captura.
- Dividir treino/validação/teste por **peça física, sessão, lote e quando viável material/câmera**, evitando que fotos rotacionadas da mesma peça apareçam em treino e teste.
- Manter conjunto de teste realmente inédito; revisar divergências entre anotadores; aplicar controle de versões a dados/modelos fora do Git público.
- As 3 imagens recebidas são **exemplos qualitativos**, não um conjunto suficiente para treinar ou avaliar.

## 5. Plano de provas antes de investimentos

| Experimento | Entrada | Saída/critério |
|---|---|---|
| P0 — ótica | peça física + alvo mínimo + diferentes luzes | comprovar visibilidade em pixels dos menores vazadores |
| P1 — segmentação | fotos anotadas, materiais/fundos distintos | comparação OpenCV vs SAM 2 vs opção treinável; IoU/Dice, falhas |
| P2 — identificação CAD | família com numerações e fotos rotacionadas | ranking e `não identificado`, sem inventar tamanho |
| P3 — microvazadores | crops originais com regiões normais/confirmadas | recuperação de furos e falsos alertas por peça/material |
| P4 — fluxo web | postos concorrentes com imagens não proprietárias/sintéticas | latência de ponta a ponta, segurança, fila, falhas, isolamento de workers |

**Não definir números de aceite sem Quality e medições de base.** A ordem dos ensaios evita gastar com treinamento/modelos antes de comprovar que a câmera enxerga os detalhes relevantes.

## 6. Estado e próximos passos

- Implementado antes desta pesquisa: Vue/FastAPI, importação DXF/HPGL, OpenCV, matching visual, módulo SAM 2 opcional sem pesos, testes sintéticos.
- Evidência de laboratório anterior: Python 3.12.16, torch 2.15.0+cpu e torchvision 0.29.2+cpu instalados no `sam2-lab/.venv`, **importação interrompida por Ctrl+C**, sem validação do modelo.
- **Nesta pesquisa:** somente documentação/decisões propostas; **nenhum código de IA, dataset ou artefato visual proprietário publicado**.
- Repriorização proposta: iniciar pelo **protocolo óptico e dataset privado** e um baseline com imagens anotadas; experimento SAM 2 ainda útil, mas não bloqueia arquitetura multiusuário e não resolve sozinho a detecção de microvazadores.
- Antes de implantar: definir requisitos de latência por posto, volume simultâneo, proteção das imagens e máquina/servidor de inferência; depois implementar contrato e worker isolado com testes.
