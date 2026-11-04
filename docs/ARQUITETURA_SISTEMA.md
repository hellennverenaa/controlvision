# Arquitetura ControlVision — atual e prevista

**Revisão:** 04/11/2026. **Cuidado:** `ATUAL` indica funcionalidade presente na branch; `FUTURO` indica proposta ainda não implementada.

## A. Arquitetura atual (protótipo local)

```text
Navegador Vue 3/TypeScript (Vite)
   | /api (proxy local)
FastAPI — backend/app/main.py
   +-- geometry.py         DXF/HPGL -> peças + entidades internas candidatas
   +-- vision.py           OpenCV -> contorno e candidatos em pixels
   +-- matching.py         correspondência visual por silhueta CAD/foto
   +-- family_matching.py  prévia de referências e numerações, sem tamanho presumido
   +-- cad_guided.py       diagnóstico óptico nas regiões CAD
   +-- microholes.py / micro_candidates.py / texture_anomalies.py
   +-- annotation_comparison.py / reference_validation.py
   +-- segmentation_contract.py / segmentation_evaluation.py
   +-- sam2_optional.py / sam2_preflight.py (opcionais; sem inferência real confirmada)
```

**API existente:**

| Rota | Papel |
|---|---|
| `GET /api/health` | Saúde / modo experimental |
| `POST /api/cad/import` | Importar DXF e HPGL/PLT/HP2 |
| `POST /api/vision/preview` | Extrair silhueta/candidatos e comparação opcional com CAD |
| `POST /api/vision/manual-regions` | Analisar marcações humanas e confirmações explícitas |
| `POST /api/vision/segmentation/preview` | Máscara OpenCV ou SAM 2 opcional |
| `POST /api/vision/segmentation/evaluate` | Comparação de máscara com referência humana revisada |

Limites de entrada e formatos estão no código e em [Contrato de segmentação](SEGMENTACAO_CONTRATO.md). As máscaras aqui são de **silhueta externa**, não segmentação dos microfuros. Matching com escala ilustrativa **não é medição física**.

## B. Arquitetura alvo para vários postos (não implantada)

```text
Operadores -> navegador/câmera da cabine
          -> HTTPS + login + API de trabalho (FastAPI)
          -> armazenamento privado de CAD/fotos/versões
          -> fila de tarefas (autorização, timeout, rastreabilidade)
          -> worker de IA central e isolado
                1) máscara externa + controle de qualidade da captura
                2) ranking da referência CAD / tipo / numeração / desconhecido
                3) inspeção de microvazadores e recortes (patches originais)
                   + busca global por sinais extras
          -> composição com CAD, regras e revisão humana
          -> histórico de resultados e auditoria
```

**Infraestrutura a decidir:** armazenamento seguro, mecanismo de fila, hardware CPU/GPU e latência por posto, banco PostgreSQL, autenticação, monitoramento, implantação e política de retenção. **Não estão implementados**. Os operadores não precisam de ambiente PyTorch ou pesos localmente.

## C. Regras funcionais de IA

- Não depender de um único modelo: OpenCV baseline, segmentador externo, reconhecimento CAD e detector de pequenos sinais são tarefas distintas.
- Modelos treináveis e SAM 2 **a avaliar**, não escolhidos como soluções definitivas. Não treinar uma nova classe para cada molde se a comparação geométrica e a recuperação por características resolverem melhor.
- O primeiro canal de inspeção usa **regiões CAD** previstas; o segundo canal é **busca global independente**, para não esconder furos extras/deslocados.
- As imagens de microvazadores devem usar pixels originais e condições ópticas adequadas; redimensionar a foto inteira pode eliminar sinais.
- `indisponivel` / `inconclusivo` são estados legítimos. Falha da IA não pode gerar máscara falsa nem decisão de aprovação.
- CAD define posição planejada, não prova que um vazador físico foi aberto. A aparência da trama tampouco prova um furo.

## D. Segurança e homologação

Não enviar moldes/fotos de fábrica para serviços externos de IA sem aprovação expressa e avaliação contratual. Separar controle de acesso por estação/trabalho, rastrear revisão CAD, versão do modelo, identificação da captura e revisor. Qualquer decisão de conformidade depende de validação física, óptica e metrológica e critérios aprovados pela Qualidade.

## E. Implementação incremental

1. Amostra física + CAD privado com revisão; protocolo óptico e referência humana.
2. Dataset privado e avaliação da silhueta existente.
3. Experimentos comparativos de máscara, matching CAD e microvazadores.
4. Serviço de inferência separado da API web e testes de concorrência/falhas.
5. Calibração, validação industrial e implantação, só após resultados.

Detalhes em [Dados e avaliação](DADOS_TREINAMENTO_VALIDACAO.md), [Plano mestre](../PLANO_DESENVOLVIMENTO.md) e [Proposta de IA sob demanda](ARQUITETURA_IA_SOB_DEMANDA.md).
