# Plano de desenvolvimento — ControlVision

**Atualizado:** 04/11/2026 · **Versão editorial:** 2.0  
**Branch:** `feat/prototipo-validacao` · **Status:** PROTÓTIPO EXPERIMENTAL, **NÃO LIBERA PRODUÇÃO**  
**Fonte para requisitos:** [docs/REQUISITOS_PRODUTO.md](docs/REQUISITOS_PRODUTO.md) · **Índice:** [docs/README.md](docs/README.md).

## Onde estamos agora

O produto será **web, acessado em vários computadores da produção**, com cabine física existente e **câmera fixa ainda não escolhida/instalada**. A IA deverá operar em serviço central (futuro). O problema real é associar a fotografia à referência CAD e **distinguir vazadores passantes minúsculos e recortes da trama normal**, sem inferir falsos furos.

**Já funciona no protótipo:** importar CAD, revisar geometrias, segmentar visualmente silhueta com OpenCV, sugerir correspondências CAD/numeração desconhecida, investigar sinais internos e revisar marcações; API/laboratório opcional de comparação de máscaras e testes sintéticos.

**Evidência real anterior:** numa lingueta clara sobre fundo azul, OpenCV exibiu silhueta plausível (25,76 ms, 960×1280), mas apresentou **15 candidatos circulares** para **3 entidades circulares por CAD**; **9 referências** sem numeração identificada; **2/3 associações ópticas ilustrativas**, não vazadores confirmados. Diferença de silhuetas 1,6% é **apenas visual**, não dimensional. SAM 2 estava indisponível e não houve máscara humana revisada nem IoU/Dice. O responsável relata que os três vazadores da peça **aparecem e são muito pequenos**, mas a dimensão exata em mm e a condição física de cada um **não foram documentadas como medição**. [Evidências](docs/EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md).

**E2.2 ainda aberta:** no laboratório `sam2-lab/.venv` fora do repositório, `uv 0.13.7`, Python 3.12.16 e **torch 2.15.0+cpu / torchvision 0.29.2+cpu foram instalados**; teste de importação interrompido com Ctrl+C; SAM 2 com pesos reais **não instalado/executado**, nenhum treinamento realizado. **Não exigir IA instalada nos postos**. [Preparação](docs/SAM2_PREPARACAO_E2.md).

**Próximo marco prioritário:** **P0 — estudo óptico + referência humana privada**, usando peça física e CAD correspondente para verificar se os menores vazadores podem ser vistos e separados da trama. Seleção da câmera comercial permanece **posterior**; não bloquear P0 por compra de equipamento.

## Roadmap e critérios

| Fase | Escopo | Estado em 04/11/2026 | Critério de conclusão |
|---|---|---|---|
| 0 — Protótipo | Vue/FastAPI, CAD, OpenCV, matching visual, diagnóstico manual | **Implementado experimentalmente** | Continuidade e testes atuais preservados |
| 1 — Infraestrutura de máscaras | Contrato, UI OpenCV/SAM2, testes sintéticos, métricas | **Concluída em código** | Sem alegar qualidade real |
| 2 — Avaliação SAM 2 | Instalação isolada, inferência e comparação com máscaras revisadas | **E2.1 concluída; E2.2+ pendentes** | Modelo executado ou decisão documentada de não adotar; métricas em fotos reais |
| P0 — Captação e visibilidade | Malha, furos físicos, iluminação, resolução | **Próxima prioridade; não executado** | Menor furo observável sob condição de captura registrada |
| 3 — Dataset privado | Fotos e CAD revisados, rótulos físicos e divisões sem vazamento | **Pendente** | Referências auditáveis e teste inédito |
| 4 — IA para silhueta | Comparar OpenCV, SAM2, modelo treinável se necessário | **Condicional / pendente** | Ganho validado ou descarte documentado |
| 5 — Referência CAD | Ranking por peça/modelo/numeração e `não identificado` | **Só prévia visual existente** | Resultados em moldes/peças não vistos e ambiguidades explícitas |
| 6 — Microvazadores/recortes | IA por patches, trama normal, CAD-guided + busca global | **Pendente** | Recall por furo, falsos alertas, casos inconclusivos medidos |
| 7 — Metrologia e qualidade | Câmera, calibração, tolerâncias e homologação | **Pendente** | Avaliação metrológica e liberação formal da Qualidade |
| 8 — Operação web | Serviço central de IA, filas, PostgreSQL, autenticação, auditoria | **Arquitetura proposta, não implantada** | Testes de segurança, concorrência e operação |

As etapas podem ter **experimentos paralelos**; P0 foi priorizado antes de investir em modelo/câmera. Etapas futuras e critérios não estão validados industrialmente.

## Próxima entrega prática (P0)

- [ ] Selecionar **uma lingueta física** e sua referência CAD/revisão em armazenamento privado.
- [ ] Identificar no CAD os vazadores passantes e recortes; confirmar **fisicamente** cada região, separando `aberto`, `incompleto/ausente` e `incerto`.
- [ ] Registrar fotos originais sem overlays, iluminação atual e, se viável, teste controlado com contraluz; **não publicar arquivos da fábrica**.
- [ ] Determinar se o **menor furo** aparece com contraste e pixels suficientes, evitando confusão com a trama; não inventar diâmetro em mm.
- [ ] Criar máscara humana revisada e comparar com OpenCV; registrar IoU/Dice apenas com essa referência.
- [ ] Definir rótulos, partição por peça física e plano inicial de dataset privado.
- [ ] Decidir próximo experimento (SAM 2 para máscara, classificador de patches de vazadores, ou melhoria óptica), com evidências.

**Protocolo:** [Cabine](docs/CABINE_CAMERA_FIXA_VAZADORES_PROTOCOLO.md) · [Treino e avaliação](docs/DADOS_TREINAMENTO_VALIDACAO.md).

## Regras permanentes

1. **Sem aprovação/reprovação industrial**, escala metrológica ou tolerância em mm por correspondência visual normalizada.
2. Cada vazador CAD esperado **não prova furo físico aberto**; cada candidato óptico **não prova defeito**; falta de sinal pode ser inconclusiva.
3. IA opcional e isolada; falhas não viram máscaras fictícias. Não alterar silenciosamente contrato/API.
4. Fotos, CADs, pesos, credenciais e dataset proprietários **nunca no GitHub público**.
5. Toda entrega: testes aplicáveis, documentação `.md` de assunto novo, atualização deste plano, **commit e push** na branch de validação. Resultados ainda não testados não podem ser marcados como concluídos.
6. PR #1 em rascunho; não mesclar `main` sem revisão.

## Registro condensado de decisões

- 19–23/10: protótipo de CAD/visão, comparação visual e laboratório de máscaras começaram; etapas 1.1–1.3 concluídas em código.
- 03/11: UI de comparação, testes de contratos e protocolo de métricas E1.4–E1.6; Python 3.12 isolado planejado e criado.
- 04/11: PyTorch CPU instalado sem teste de importação concluído; discussão de IA no servidor e pesquisa de segmentação/anomalias/rotulagem.
- 04/11: requisitos confirmados — **furos passantes CAD, tramas complexas, cabine pronta sem câmera, operação web multi-posto**; capturas anteriores analisadas como evidência qualitativa.
- 04/11: **revisão editorial 2.0**; centralizados requisitos, arquitetura, dados e progresso, removendo documentação redundante e detalhes antigos da capa. Histórico integral continua nos commits anteriores.

Para decisões, comandos, experimentos e resultados pormenorizados, usar [índice de documentação](docs/README.md) e histórico Git. Revisão editorial **não equivale a novo teste, treinamento ou implantação**.
