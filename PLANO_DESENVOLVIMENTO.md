# PLANO DE DESENVOLVIMENTO — ControlVision

> **Documento vivo e fonte principal de acompanhamento do projeto.**  
> Atualizado em: **04/11/2026** · Versão do plano: **1.8**  
> Branch de trabalho: `feat/prototipo-validacao` · Estado: **PROTÓTIPO EXPERIMENTAL — NÃO LIBERA PRODUÇÃO**
>
> **Procedimento de entregas GitHub:** ver [`docs/FLUXO_TRABALHO_GITHUB.md`](docs/FLUXO_TRABALHO_GITHUB.md). Cada mudança deve incluir documentação `.md` específica para assuntos novos, atualização deste plano, testes cabíveis, commit e push na branch de validação. **E2.2 permanece pendente da execução local pelo operador.**
>
> **Regra de continuidade:** antes de iniciar uma alteração, ler a seção **"Onde estamos agora"**; depois de concluir uma entrega, atualizar as caixas de seleção, as evidências, a data e o histórico deste arquivo **no mesmo conjunto de alterações do código**. Não declarar etapas concluídas apenas porque o código foi escrito: exigir teste e revisão dos resultados.

## 1. Objetivo do projeto

Construir um sistema de inspeção visual de componentes cortados para calçados, capaz de:

1. Importar CAD (`DXF` e `HPGL/PLT`) com peças, numerações e geometrias internas.
2. Fotografar uma peça cortada e **segmentar sua silhueta**, com diferentes materiais e fundos.
3. Sugerir qual contorno do CAD corresponde à peça da fotografia, **sem inventar numeração**.
4. Investigar a presença e a posição de vazadores/recortes, inclusive em malhas texturizadas.
5. **Somente após calibração e validação metrológica**, comparar dimensões com o CAD usando critérios definidos com a Qualidade.

**Estratégia acordada:** sistema híbrido. **IA** para interpretação visual e segmentação; **OpenCV + geometria CAD** para alinhamento e correspondência; um **modelo especializado posterior** para os microvazadores. Não treinar uma classe nova para cada modelo de calçado se for possível reconhecer moldes novos pela sua geometria.

### Fora do escopo nesta fase

- Compra de câmera industrial, iluminação ou infraestrutura de produção.
- Definição unilateral de tolerâncias de corte/posicionamento.
- Aprovação/reprovação automática de peças para produção.
- Banco PostgreSQL, autenticação corporativa e hospedagem de produção (previstos **após** a validação).
- Alegar medidas em mm a partir de encaixes com escala normalizada.

## 2. Onde estamos agora

**Fase atual: ETAPA 2 — E2.1 concluída; E2.2 em preparação no computador do operador.**  
**Última evidência local (03/11/2026):** Ubuntu **26.04.1 LTS**, Python do sistema **3.14.4**; comandos `python3.12`, `python3.11` e `python3.13` não encontrados. **14 GiB de RAM total; apenas 4,2 GiB disponíveis no momento; swap de 4 GiB com 2 GiB em uso.** `nvidia-smi` indisponível (**GPU NVIDIA não confirmada, não é prova de ausência de GPU**). Preflight do SAM 2: desativado, sem torch/torchvision/sam2 ou pesos. **Nenhum modelo real executado.**  
**Ocorrência de instalação (03/11/2026):** `uv` ainda não encontrado; tentativa de instalação via Snap bloqueada por requisito de `classic confinement` (e tentativa inicial com falha de autenticação). Recomendada instalação standalone oficial da Astral **sem sudo**, registrada em `docs/SAM2_PREPARACAO_E2.md`. **Aguardando confirmação de `uv --version`; nenhuma instalação concluída nem IA executada.**  
**Novo resultado do operador (03/11/2026):** instalação standalone do `uv` confirmada no diretório do usuário (`~/.local/bin`), versão **0.13.7** (`x86_64-unknown-linux-gnu`). O erro ao digitar `uv 0.x.x` foi apenas tentativa de executar texto ilustrativo, sem impacto na instalação. **Ainda pendente:** instalar Python 3.12 com `uv`, criar/verificar `sam2-lab/.venv` e conferir RAM/disco. Ver `docs/SAM2_PREPARACAO_E2.md`.  
**Evidência nova do operador (03/11/2026):** `uv python install 3.12` instalou **CPython 3.12.16**; `sam2-lab/.venv` foi criado e ativado fora do repositório, com `which python` confirmado. `free -h`: 14 GiB RAM total, 4,5 GiB disponíveis; **swap de 4 GiB praticamente toda utilizada (17 MiB livres)**. `df -h`: 31 GiB livres na partição raiz (79% de uso). **Subetapa de criação do ambiente concluída; E2.2 geral aberta.** Antes de instalar PyTorch/SAM 2, revisar processos de maior consumo e swap por comandos somente de leitura. Evidência e roteiro em `docs/SAM2_PREPARACAO_E2.md`.  
**Novo diagnóstico local (04/11/2026):** RAM disponível caiu para **2,5 GiB**, swap utilizada **3,9/4 GiB**, disco **31 GiB livres**. Processo `Isolated Web Co` de maior consumo apresenta **4.761.624 KiB RSS (~4,54 GiB)**; provável conteúdo isolado do Firefox, sem identificação da aba/causa. Antes de instalar IA, salvar trabalho, reduzir abas do navegador voluntariamente e repetir o diagnóstico; **não** usar `kill`/`swapoff` automaticamente. Detalhes e comandos em [`docs/SAM2_DIAGNOSTICO_MEMORIA_E2.md`](docs/SAM2_DIAGNOSTICO_MEMORIA_E2.md). **E2.2 continua aberta.**  
**Segunda coleta de recursos (04/11/2026):** RAM disponível subiu para **3,2 GiB** (antes 2,5), swap em uso caiu para **2,6 GiB** (antes 3,9). No `vmstat 1 5`, amostras intermediárias mostraram `si=732` e `si=20` KiB/s, `so=0` e amostras finais `si=so=0` — sem indicação de troca contínua intensa nesse intervalo. Processo `Isolated Web Co` ainda com **4.751.372 KiB RSS (~4,53 GiB)**. Prioridade: salvar sessão e encerrar Firefox normalmente, quando possível, depois repetir RAM/processos; não forçar encerramento ou swapoff. Ver `docs/SAM2_DIAGNOSTICO_MEMORIA_E2.md`. **Sem PyTorch/SAM 2 instalado e E2.2 aberta.**  
**Terceira coleta (04/11/2026):** depois de reduzir o consumo do navegador, **9,1 GiB de RAM disponíveis** (antes 3,2 GiB), **1,9/4 GiB de swap usados** (antes 2,6 GiB); o processo de ~4,5 GiB RSS não aparece mais entre os 10 maiores. Ambiente tornou-se mais favorável, embora inferência CPU não esteja comprovada. **Próxima ação: instalar apenas PyTorch + TorchVision CPU-only no `sam2-lab/.venv`, verificar importação, versões e RAM/disco; ainda sem SAM 2/pesos.** Procedimento em `docs/SAM2_PREPARACAO_E2.md` e evidência em `docs/SAM2_DIAGNOSTICO_MEMORIA_E2.md`. **E2.2 aberta.**  
**Evidência da instalação CPU-only (04/11/2026):** `uv pip install` no `sam2-lab/.venv` instalou **torch 2.15.0+cpu** e **torchvision 0.29.2+cpu**. O teste `import torch, torchvision` foi interrompido por **Ctrl+C** durante `import torch` (`KeyboardInterrupt`), portanto importação/tensor **não verificados**, sem prova de incompatibilidade. Último recurso informado: **8,2 GiB** RAM disponível, swap **1,9 GiB** utilizada e disco **31 GiB** disponíveis. **Decisão de produto a confirmar:** IA sob demanda no servidor próprio ou API externa, sem exigir modelo no computador do operador; suspender downloads de SAM 2 até a decisão. Proposta e requisitos em [`docs/ARQUITETURA_IA_SOB_DEMANDA.md`](docs/ARQUITETURA_IA_SOB_DEMANDA.md). **E2.2 ainda aberta.**  
**Pesquisa orientada ao caso real (04/11/2026):** três fotos de lingueta branca sobre fundo azul evidenciam trama com aberturas regulares que não devem ser classificadas como vazadores; orientações distintas reforçam necessidade de reconhecimento da referência CAD com numeração ambígua e de inspeção de recortes/microvazadores por patches na resolução original. Projetos públicos estudados: SAM 2, Anomalib (PatchCore/EfficientAD), CVAT, DINOv2, Ultralytics e servidores de inferência. Documento específico: [`docs/PESQUISA_IA_INSPECAO_TRAMAS_CAD_2026-11-04.md`](docs/PESQUISA_IA_INSPECAO_TRAMAS_CAD_2026-11-04.md). **Decisão proposta:** separar 3 tarefas (máscara, identificação CAD, inspeção de pequenas estruturas), formar dataset privado revisado e validar ótica/câmera antes de treinar. **Não foi treinada/executada IA e fotos não foram publicadas.**  
**Requisitos de chão de fábrica confirmados (04/11/2026):** vazadores são **furos passantes minúsculos previstos no CAD** e podem falhar devido ao corte da máquina; existem DXFs correspondentes com geometrias internas; captura será por **câmera fixa em cabine muito iluminada**, com aplicação web para vários postos. Plano P0: comparar iluminação frontal e contraluz mantendo a peça parada, verificar visibilidade dos menores furos frente à trama, revisar fisicamente vazadores e recortes e registrar pares CAD/foto em dataset privado. A escolha da luz e qualquer treinamento ainda dependem de ensaio. Protocolo detalhado: [`docs/CABINE_CAMERA_FIXA_VAZADORES_PROTOCOLO.md`](docs/CABINE_CAMERA_FIXA_VAZADORES_PROTOCOLO.md). **Sem instalação nova, execução de IA ou validação física nesta entrega.**  
**Evidências históricas e estado da cabine (04/11/2026):** cabine física existente, **câmera ainda não instalada/escolhida**, decisão reservada para etapa posterior. Capturas e relatório de teste anterior com lingueta clara/fundo azul: silhueta OpenCV `ok` (25,76 ms em 960×1280), **15 candidatos circulares** frente a **3 entidades circulares por referência CAD**, **9 referências** comparadas sem numeração identificada, **2/3 associações ilustrativas**, divergência de silhueta **1,6% apenas visual**; V01/V03 com sinal suspeito, V02 inconclusivo; SAM 2 indisponível, sem máscara humana revisada/IoU/Dice. Não representa identificação ou verificação física de vazadores. Detalhes em [`docs/EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md`](docs/EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md). **Próxima prioridade: identificar vazadores fisicamente e anotar dados originais privados; escolha da câmera permanece posterior.**  
**Próxima ação concreta: E2.2** — criar laboratório **isolado fora do ControlVision**, utilizando `uv` para instalar **Python 3.12 por usuário** e criar `~/Documentos/ambiente_dass/sam2-lab/.venv` (sem modificar o Python 3.14). Só então avaliar bibliotecas CPU-only e checkpoint `tiny`; verificar memória/disco e medir recursos antes da inferência. **Não instalar PyTorch no backend principal e não declarar E2.2 concluída.** Guia: `docs/SAM2_PREPARACAO_E2.md`.

| Etapa | Tema | Estado | Condição para avançar |
|---|---|---|---|
| 0 | Base existente do ControlVision | ✅ Base implementada, **não homologada** | Testes de regressão existentes preservados |
| 1 | Preparação para IA + baseline do OpenCV | ✅ **INFRAESTRUTURA E TESTES SINTÉTICOS CONCLUÍDOS** (sem validação real) | Comparação reproduzível definida |
| 2 | Testar SAM 2 pré-treinado | 🚧 **EM EXECUÇÃO (E2.2 aguardando preparo local)** | Avaliação documentada contra OpenCV |
| 3 | Preparar conjunto privado de imagens anotadas | ⬜ Pendente | Imagens e máscaras revisadas + divisão por peça física |
| 4 | Treinar e avaliar U-Net, **se justificado** | ⬜ Condicional | Melhoria demonstrada em fotos nunca vistas |
| 5 | Reconhecimento do molde CAD a partir da máscara | ⬜ Pendente | Ranking correto e opção "não identificado" |
| 6 | IA específica para vazadores | ⬜ Pendente | Avaliação própria de recuperação e falsos alertas |
| 7 | Calibração dimensional e validação metrológica | ⬜ Pendente | Evidências de calibração e critérios da Qualidade |
| 8 | Persistência, segurança e implantação | ⬜ Pendente | Só após provas de viabilidade e requisitos aprovados |

**Legenda:** ✅ entregue com ressalvas; ⏭️ foco imediato; ⬜ não iniciado; 🚧 em execução; ⛔ bloqueado; ↪️ condicional. A caixa `[x]` só marca a tarefa explicitamente verificada, não a etapa industrial como um todo.

### 2.1 O que já está disponível (Etapa 0)

- [x] Aplicação Vue 3 + TypeScript + Vite, backend Python + FastAPI.
- [x] Importação experimental de DXF e HPGL, incluindo múltiplas peças e referências.
- [x] Revisão humana das geometrias internas: círculos do CAD não são automaticamente vazadores reais.
- [x] Upload de fotografia, webcam e segmentação heurística com OpenCV.
- [x] Sobreposição CAD × fotografia por contorno, com **escala visual normalizada**.
- [x] Prévia de múltiplas numerações sem selecionar uma delas como verdadeira.
- [x] Diagnóstico de vazadores: candidatos circulares, micropontos e regiões guiadas pelo CAD.
- [x] Modo de validação com referências confirmadas fisicamente pelo operador.
- [x] Análise **exploratória** de contraste irregular em escalas de 5, 9 e 15 px.
- [x] Testes automatizados de backend e compilação do frontend nas alterações anteriores.
- [ ] Homologação para uso industrial — **não iniciada; depende das etapas 6 e 7**.

**Caso real de referência (lingueta QUEST 7, relatório anterior):** três vazadores confirmados pela pessoa que examinou fisicamente a peça; dois tiveram candidato global próximo em uma captura (**2/3 = 66,7% de recuperação somente das três referências anotadas**), um não teve candidato; surgiram **13 candidatos automáticos sem associação**, que **não podem ser chamados automaticamente de falsos positivos**. V01 apresentou sinal irregular incomum; V02 e V03 não se distinguiram da trama na análise multiescala. A sobreposição visual das silhuetas exibiu cerca de **1,6% de divergência com normalização de escala — NÃO é erro dimensional da peça**. A numeração continua desconhecida.

**Restrições do caso:** uma única peça física, fotografias limitadas, furos minúsculos e trama têxtil; resultado insuficiente para afirmar sensibilidade, especificidade ou precisão industrial.

## 3. Etapas e critérios de conclusão

### ETAPA 1 — Preparar a infraestrutura experimental de IA e o baseline

**Meta:** testar modelos sem alterar o comportamento atual nem exigir GPU para usar o projeto diariamente.

- [x] E1.1 Definir um contrato de saída para segmentação (máscara binária, largura/altura, método, tempo de execução, avisos), independentemente do algoritmo. **Contrato v1 em `backend/app/segmentation_contract.py` e `docs/SEGMENTACAO_CONTRATO.md`; máscara PNG binária validada e endpoint opt-in.**
- [x] E1.2 Preservar OpenCV como caminho padrão e manter o fluxo atual totalmente funcional. **Rotas antigas preservadas; regressão e CI de backend/frontend aprovados.**
- [x] E1.3 Criar módulo experimental **isolado do fluxo padrão no código** para inferência SAM 2 opt-in, com falha controlada quando modelo/pesos não estiverem instalados. **`backend/app/sam2_optional.py`, rota experimental, testes de indisponibilidade/máscara simulada e CI aprovados.** Isolamento é por módulo + thread, **não por processo**; pesos reais não testados.
- [x] E1.4 Preparar visualização **lado a lado** da fotografia, máscara OpenCV e máscara SAM 2 na Etapa 3 do Vue, sem substituir a referência atual. **Botão opt-in; estados indisponível/inconclusivo; respostas antigas invalidadas ao trocar foto/tom/molde; frontend compilado e testes backend aprovados.**
- [x] E1.5 Criar testes sintéticos de contrato, integração, ausência de pesos e regressão. **`frontend/tests/segmentation-comparison.test.mjs`: 12 testes novos da comunicação, respostas independentes, contrato, estados inconclusivos, identidade de método, PNG, concorrência e descarte de resultados obsoletos; integrados ao `npm run build`. Backend mantém testes de pesos/dependências ausentes e regressão. CI aprovado.** Testes de UI em navegador real e execução de pesos reais ainda não realizados.
- [x] E1.6 Definir e implementar protocolo reproduzível para IoU, Dice, erro médio/p95 de borda (pixels), tempo por método e falhas sem máscara. **`backend/app/segmentation_evaluation.py`, `POST /api/vision/segmentation/evaluate`, upload de PNG revisado no Vue, testes sintéticos e `docs/SEGMENTACAO_METRICAS.md`; CI backend/frontend aprovado.** Sem máscara revisada, nenhuma pontuação é calculada; SAM 2 indisponível = `nao_medido`, não IoU 0. **Não houve avaliação com referências humanas reais.**

**Entregável:** aplicação atual preservada + interface/API para ensaio comparativo, inicialmente sem promessas de melhor desempenho.

**Parcial em 23/10/2026 (E1.1–E1.3):** `POST /api/vision/segmentation/preview` suporta `method=opencv` e `method=sam2`. OpenCV continua padrão; SAM 2 só roda se `CONTROLVISION_SAM2_ENABLED=1`, variante válida, checkpoint local e bibliotecas disponíveis. Se não estiver habilitado, retorna contrato v1 com **`status=indisponivel`**, sem máscara nem fallback silencioso. Um prompt de caixa vem do **contorno OpenCV** (IA ainda não independente). Executa em thread de trabalho com lock, não em processo isolado. CI backend/frontend aprovado, com testes simulados de máscara, pesos ausentes, dependências e regressão. **Nenhum modelo real instalado/executado, fotografia real avaliada ou métrica de qualidade medida.** Documentação: `docs/SEGMENTACAO_CONTRATO.md` e `docs/SAM2_EXECUCAO_EXPERIMENTAL.md`. **E1.5 ainda pendente** até completar testes de interface e ensaios posteriores.

**Parcial em 03/11/2026 (E1.4):** `frontend/src/App.vue` apresenta um laboratório de máscaras com três painéis (fotografia original, OpenCV e SAM 2), acionado pelo operador **após** carregar uma foto. Uma chamada `method=sam2` desativada exibe `indisponivel` no painel, sem máscara. Erros independentes de rede são mostrados separadamente, preservando o resultado da outra abordagem. Respostas de requisições antigas são descartadas após mudança de fotografia, modo, tom ou referência CAD. **Não é avaliação de qualidade**, não há máscara humana revisada ou execução real SAM 2; a contagem de vazadores e o fluxo CAD continuam inalterados. A compilação Vue e os testes backend passaram. **E1.5 permanece aberta** porque ainda faltam testes automatizados de comportamento da interface (especialmente concorrência e estado obsoleto).

**Parcial em 03/11/2026 (E1.5):** a lógica de transporte e controle de versão da requisição foi extraída para `frontend/src/segmentationComparison.ts`, compartilhada pela interface. O runner descarta uma comparação inteira quando chega depois de uma nova fotografia/configuração; erro de um método não apaga resultado válido do outro. A resposta é validada quanto a status, método, versão, forma do contrato e cabeçalho/dimensões do PNG. **Não é validação completa do arquivo PNG** (o navegador faz decodificação). Os 12 testes do frontend rodam automaticamente no `npm run build` usando `node:test` com respostas sintéticas; CI de frontend e backend aprovado. **Não foram executados teste end-to-end no navegador, inferência SAM 2 real nem comparação quantitativa de máscaras.**

**Parcial em 03/11/2026 (E1.6):** o protocolo de métricas foi implementado em `backend/app/segmentation_evaluation.py` e documentado em `docs/SEGMENTACAO_METRICAS.md`. Na Etapa 3, o operador pode anexar PNG binário 8-bit (mesma resolução da fotografia) e **declarar revisão humana** antes de avaliar. A API opt-in **reexecuta** OpenCV e SAM 2 na mesma fotografia/configuração. IoU/Dice e distância simétrica média/p95 de bordas só são produzidos para máscaras válidas; ausência de máscara, indisponibilidade e inconclusão resultam em `nao_medido` e `metrics=null` — nunca falso zero de acerto. Tempos continuam de processamento, sem upload. Os testes sintéticos cobrem identidade, deslocamento, não sobreposição, referência inválida, ausência de confirmação humana e IA indisponível. **Nenhuma máscara humana real foi usada; não há resultados de precisão, tolerância ou confiabilidade industrial.** CI: [backend/frontend aprovados](https://github.com/hellennverenaa/controlvision/actions/runs/41673813764). **A ETAPA 1 encerra somente a infraestrutura de ensaio**, não os testes de reconhecimento real.

**Para encerrar:** testes passando e comparação reproduzível; nenhum aumento não explicado de falhas no fluxo atual.

### ETAPA 2 — Avaliar SAM 2 pré-treinado (sem treinar do zero)

**Meta:** descobrir se um modelo existente já melhora a extração do contorno da peça.

- [x] E2.1 Verificar licença dos pesos, dependências, requisitos de CPU/GPU e requisitos para avaliar custo de execução. **Fontes oficiais consultadas e registradas em `docs/SAM2_PREPARACAO_E2.md`; recomendação inicial SAM 2.1 `tiny`, licença Apache-2.0 e pareamento variante/configuração/checkpoint confirmado. `backend/app/sam2_preflight.py` faz verificação estática local sem downloads/importação de torch; executor rejeita nome de checkpoint incompatível. Novos testes aprovados em CI.** **Custo, tempo, RAM/VRAM e compatibilidade GPU reais não medidos; medição em E2.2.**
- [ ] E2.2 Executar SAM 2 de maneira **opcional** em ambiente local de experimento, sem iniciar automaticamente no servidor principal. **Diagnóstico inicial local recebido em 03/11/2026 (Linux/Python 3.14, desativado, sem torch/torchvision/sam2/checkpoint); primeiro verificar Python alternativo, GPU e RAM. Não concluído.**
- [ ] E2.3 Usar caixa da peça/indicações vindas do OpenCV ou cliques do operador como *prompts*, documentando o nível de intervenção humana.
- [ ] E2.4 Comparar máscara SAM 2 com OpenCV **nas mesmas fotos**, contra máscaras corrigidas por pessoa.
- [ ] E2.5 Registrar casos bons e ruins: fundo azul, tecido claro, malha, rotações, sombras, recortes próximos à borda.
- [ ] E2.6 Decidir: **adotar como auxiliar**, **usar só para anotar dados** ou **não utilizar**.

**Parcial em 03/11/2026 (E2.1):** verificação documental concluída com fontes da Meta. `docs/SAM2_PREPARACAO_E2.md` registra Apache-2.0 (código/checkpoints), Linux/Python ≥3.10, PyTorch ≥2.5.1 e torchvision compatível, fontes de checkpoints SAM 2.1 e riscos de GPU/CPU. O comando `cd backend && python -m app.sam2_preflight` verifica configurações, módulos/versões e existência/pareamento de checkpoint **sem instalar, ler pesos, importar torch ou iniciar IA**; testes sintéticos de preflight e rejeição de checkpoint incompatível passaram no CI. **Nome de arquivo não comprova integridade/autenticidade; o preflight não garante que o modelo conseguirá executar.** **RAM, VRAM, latência e custo não medidos**; serão avaliados com hardware real em E2.2. OpenCV, CAD e vazadores permanecem inalterados. **Sem foto real avaliada, sem IoU/Dice de IA.**

**Observação E2.2 — ambiente real do operador (03/11/2026):** o comando documentado `python -m app.sam2_preflight` não existia no Linux porque o sistema só disponibiliza `python3`. A execução correta `python3 -m app.sam2_preflight` retornou JSON com Python 3.14, Linux, `CONTROLVISION_SAM2_ENABLED` desligado, `torch`, `torchvision` e `sam2` ausentes e checkpoint `sam2.1_hiera_tiny.pt` não encontrado. O dispositivo `cpu` é **configuração padrão**, não evidência de inexistência de GPU NVIDIA. **Nenhuma instalação ou teste real de IA foi realizado.** Próximo diagnóstico: versões alternativas de Python, tipo de GPU e RAM. Não marcar E2.2 concluída antes de executar pesos oficiais e validar pelo menos uma fotografia.

**Para encerrar:** tabela objetiva de métricas e limitações; decisão registrada. Resultado melhor em apenas uma foto não basta.

### ETAPA 3 — Formar conjunto de dados privado, auditável e revisado

**Meta:** possuir dados confiáveis antes de treinar nossa própria IA.

- [ ] E3.1 Definir padrão de diretórios privados, metadados e versão do conjunto de dados.
- [ ] E3.2 Registrar fotografias **originais**, material, tipo de peça, orientação, fundo/iluminação, identificação da **peça física** e CAD conhecido (quando houver).
- [ ] E3.3 Permitir criar/corrigir máscaras da **silhueta externa** com revisão humana.
- [ ] E3.4 Armazenar separadamente anotações de vazadores físicos e marcações ópticas. **Não usar círculo CAD como prova de furo físico**.
- [ ] E3.5 Formar coleção inicial de referência (objetivo exploratório: ~80–150 fotos, se houver diversidade real; quantidade a revisar após a coleta).
- [ ] E3.6 Dividir treino/validação/teste por **peça física**, evitando que a mesma peça apareça em conjuntos diferentes só por rotação ou fotografia repetida.
- [ ] E3.7 Revisar qualidade das anotações, casos ambíguos, autorização de uso e privacidade.

**Para encerrar:** dataset documentado, máscaras verificadas, partições congeladas e reproduzíveis.

**Segurança:** repositório público. **NÃO enviar fotografias reais, CADs proprietários, máscaras associadas a produto, modelos treinados sobre dados confidenciais ou credenciais ao GitHub.** Usar armazenamento local/privado fora do repositório e regras adequadas de exclusão no Git.

### ETAPA 4 — Treinar U-Net com PyTorch (condicional)

**Iniciar apenas após as Etapas 2 e 3 indicarem necessidade e dados suficientes.**

- [ ] E4.1 Selecionar arquitetura leve U-Net, pesos iniciais e licença compatível com uso interno.
- [ ] E4.2 Criar scripts de treinamento e inferência separados do FastAPI.
- [ ] E4.3 Usar *transfer learning* e aumentos moderados de dados, sem causar vazamento entre conjuntos.
- [ ] E4.4 Registrar versões de código/dataset, hiperparâmetros, sementes, checkpoints e métricas.
- [ ] E4.5 Avaliar **somente no conjunto de teste não utilizado no treinamento ou na seleção do modelo**.
- [ ] E4.6 Comparar U-Net × SAM 2 × OpenCV usando mesmas imagens e critérios.
- [ ] E4.7 Adotar modelo apenas se a melhora for relevante, repetível e viável em tempo de execução.

**Para encerrar:** evidência de ganho em imagens novas **ou decisão documentada de não adotar**, sem maquiar resultados.

### ETAPA 5 — Reconhecer a peça usando geometria CAD

**Meta:** reconhecer moldes novos por forma, sem depender de treinar uma classe para cada modelo de calçado.

- [ ] E5.1 Transformar a máscara segmentada em contorno adequado ao comparador CAD existente.
- [ ] E5.2 Comparar e ranquear contornos CAD com invariância controlada de orientação e deslocamento.
- [ ] E5.3 Avaliar objetos parecidos, inversão/espelhamento, peças sobrepostas, fundo contaminado e contorno incompleto.
- [ ] E5.4 Oferecer **"não identificado / múltiplas hipóteses"**, com justificativa visual e revisão humana.
- [ ] E5.5 Testar novos desenhos DXF que **não participaram do treinamento**.
- [ ] E5.6 Separar reconhecimento de **tipo/formato** de determinação de **numeração/tamanho**.

**Para encerrar:** demonstrar correspondência de forma com ranking correto em conjunto de teste e rejeição de desconhecidos. Sem calibração física, **não determinar tamanho em mm ou numeração pela escala visual**.

### ETAPA 6 — Desenvolver IA especializada em vazadores

**Somente depois de termos imagens/máscaras que realmente mostrem furos suficientemente visíveis.**

- [ ] E6.1 Construir conjunto separado de recortes com **vazador físico confirmado**, trama sem vazador, manchas, sombras e amostras inconclusivas.
- [ ] E6.2 Garantir negativos próximos aos furos verdadeiros e materiais variados; confirmar rótulos fisicamente.
- [ ] E6.3 Comparar classificador/segmentador de recortes com as heurísticas atuais sem alterar os limiares apenas para "encontrar três".
- [ ] E6.4 Combinar busca **guiada pelo CAD** com investigação **global** de vazadores deslocados/extras.
- [ ] E6.5 Medir recuperação de furos reais, falsos alertas em negativos revisados e casos inconclusivos em fotos novas.
- [ ] E6.6 Investigar especificamente V02: se não houver informação óptica suficiente, registrar limitação, sem inventar detecção.

**Para encerrar:** evidência em várias peças físicas, materiais e sessões de captura; critérios de confiabilidade definidos **antes** da homologação.

### ETAPA 7 — Metrologia e critérios com a Qualidade

- [ ] E7.1 Definir e validar sistema óptico e iluminação, somente quando a viabilidade do reconhecimento justificar.
- [ ] E7.2 Implementar calibração de pixels para dimensões físicas, distorção óptica e perspectiva.
- [ ] E7.3 Medir repetibilidade, incerteza, erros de borda e posicionamento.
- [ ] E7.4 Definir com a Qualidade tolerâncias e critérios de aceitação/rejeição.
- [ ] E7.5 Realizar ensaios cegos e avaliar riscos de falsos aceites/falsas rejeições.
- [ ] E7.6 Liberar funcionalidades industriais **somente se formalmente homologadas**.

### ETAPA 8 — Dados, infraestrutura e operação

- [ ] E8.1 Projetar persistência em **PostgreSQL**, com histórico e versões dos resultados.
- [ ] E8.2 Implementar autenticação/autorização e trilha de auditoria.
- [ ] E8.3 Definir implantação corporativa, monitoramento, segurança e backup.
- [ ] E8.4 Criar versionamento e reversão de modelos treinados (*model registry* ou equivalente).
- [ ] E8.5 Validar desempenho e estabilidade do fluxo operacional.
- [ ] E8.6 Elaborar procedimentos de operação, revalidação e manutenção.

## 4. Como avaliar cada mudança (regras permanentes)

1. **Comparação justa:** toda inovação precisa ser comparada com o baseline OpenCV na mesma amostra; indicar se houve anotação humana ou *prompt*.
2. **Não confundir métricas:** IoU da máscara, sobreposição CAD normalizada, recuperação de vazadores e erro em mm são grandezas diferentes.
3. **Não contar marcação como detecção:** clique do operador, posição prevista no CAD e contraste suspeito não são vazadores detectados automaticamente.
4. **Controle de falsos alertas:** candidato fora das marcações não é necessariamente falso positivo; negativos precisam de verificação humana.
5. **Generalização:** nunca avaliar um modelo como "generalizado" se as imagens de teste vierem das mesmas peças físicas do treino.
6. **Sem aprovação industrial:** manter avisos e restrições atuais até a Etapa 7.
7. **Licenças:** conferir licenças de código e de pesos de IA antes de incorporar dependências ou modelos.
8. **Retrocompatibilidade:** novas rotas de IA não devem impedir a análise OpenCV quando estiverem desativadas ou indisponíveis.

## 5. Registro das experiências e evidências

Adicionar uma linha por rodada relevante. Se não houver dados, escrever **"não medido"**, nunca inventar números.

| Data | Experimento / referência | Método | Resultado principal | Evidência / próxima decisão |
|---|---|---|---|---|
| 21/10/2026 | Lingueta QUEST 7; 3 furos físicos declarados pelo operador | OpenCV + CAD + anotações | Relatório de uma captura: **2/3** com candidato próximo; **13** candidatos sem associação; V02 ainda inconclusivo | Base anterior documentada no README; **não é métrica industrial** |
| 21/10/2026 | Sinais irregulares guiados pelo CAD | *Black-hat* multiescala | V01 com contraste incomum; V02 e V03 sem destaque suficiente | Manter como diagnóstico separado da detecção global |
| 22/10/2026 | Planejamento de IA | Revisão de arquitetura | Adotar abordagem **OpenCV baseline → SAM 2 → dataset privado → U-Net condicional** | E1.1 executada em 23/10; **próxima: E1.3** |
| 23/10/2026 | Segmentação v1, só OpenCV | Máscara PNG/base64 com dimensões, contorno, método, tempo e avisos; endpoint opcional | Backend e frontend aprovados no GitHub Actions; **nenhuma imagem real testada**; **nenhuma IA executada** | [CI](https://github.com/hellennverenaa/controlvision/actions/runs/39945290274); `backend/tests/test_segmentation_contract.py`; E1.1/E1.2 concluídas |
| 23/10/2026 | SAM 2 opt-in (E1.3) | Executor de inferência opcional em thread, prompt de caixa do OpenCV, máscaras simuladas para testar integração | Backend e frontend aprovados; sem instalação de modelo e sem validação óptica real; ausências retornam `indisponivel` | [CI](https://github.com/hellennverenaa/controlvision/actions/runs/39947241641); `backend/tests/test_sam2_optional.py` |
| 03/11/2026 | Visualização OpenCV × SAM 2 (E1.4) | Etapa 3: fotografia original, máscara binária OpenCV e máscara SAM 2 opcional, com estados explícitos | Compilação frontend e testes backend aprovados; nenhuma inferência real de SAM 2 nem avaliação de qualidade de máscara; medições **não realizadas** | [CI](https://github.com/hellennverenaa/controlvision/actions/runs/41654017596); `frontend/src/App.vue` |
| 03/11/2026 | Teste manual apresentado pelo operador | Foto da lingueta em malha branca, fundo azul, 960 × 1280 px | OpenCV: máscara produzida, **30,66 ms** informados; SAM 2: **indisponível**, desativado. Detector geral: **15 candidatos circulares**, NÃO 15 furos. Nove CADs testados por forma; sobreposição ilustrativa ~**1,6%** | Captura e relatório enviados na conversa, **não versionados no GitHub**; nenhuma medida em mm, IoU/Dice ou avaliação SAM 2 |
| 03/11/2026 | E1.5 — testes automatizados de comparação | Módulo frontend com solicitações concorrentes, validação de contrato e rejeição de respostas obsoletas | **12 testes novos passaram**, backend existente e build Vue aprovados. **Sem teste end-to-end de navegador ou pesos SAM 2 reais.** | [CI](https://github.com/hellennverenaa/controlvision/actions/runs/41655868378); `frontend/tests/segmentation-comparison.test.mjs` |
| 03/11/2026 | E1.6 — avaliação de silhuetas com máscara humana | IoU, Dice, distância simétrica média/p95 de borda, tempo e estado de falha, interface/API com PNG binário e confirmação de revisão | **Backend e frontend aprovados com testes sintéticos**, imagem real não avaliada; nenhuma métrica de IA real ou conclusão metrológica | [CI](https://github.com/hellennverenaa/controlvision/actions/runs/41673813764); `docs/SEGMENTACAO_METRICAS.md` |
| 03/11/2026 | E2.1 — revisão SAM 2.1 e preflight local | Meta Apache-2.0, Python ≥3.10, torch ≥2.5.1, torchvision compatível; checkpoint `tiny` e variantes oficiais; checagem de pacote e nome de pesos sem execução | Backend e frontend aprovados; **pesos não baixados, IA real não executada, GPU/memória/latência/custo não medidos** | [CI](https://github.com/hellennverenaa/controlvision/actions/runs/41675036555); `backend/tests/test_sam2_preflight.py`; `docs/SAM2_PREPARACAO_E2.md`; **próxima: E2.2** |

| 03/11/2026 | Diagnóstico local E2.2 no Linux do operador | `python3 -m app.sam2_preflight` | Python **3.14**, IA **desativada**, `torch`/`torchvision`/`sam2` ausentes e checkpoint não configurado. Dispositivo selecionado: `cpu`; GPU física não verificada. **Nenhuma inferência executada.** | Resultado textual informado pelo operador; verificar opções de Python, GPU e RAM antes de instalar dependências. |
| 03/11/2026 | Inventário de hardware E2.2 | `cat /etc/os-release`, `free -h`, alternativas Python e `nvidia-smi` | Ubuntu **26.04.1**, Python **3.14.4**, 14 GiB RAM total, **4,2 GiB disponíveis**, **2/4 GiB de swap em uso**, `python3.12/3.11/3.13` ausentes, NVIDIA **não confirmada**. Desempenho do SAM 2 **não medido**. | **Decisão:** laboratório Python 3.12 independente via `uv`; uso de CPU apenas como teste conservador, sem downloads pesados até preparar ambiente. `docs/SAM2_PREPARACAO_E2.md`; **E2.2 aberta**. |

**Modelo para novos registros:** `AAAA-MM-DD | conjunto/fotos e quantidade de peças físicas | método/versão | métricas + casos falhos | commit/PR/teste + decisão`.

## 6. Impedimentos e decisões pendentes

| Item | Situação | Como resolver sem interromper o avanço |
|---|---|---|
| Poucas fotos e um material principal | ⚠️ Insuficiente para alegar generalização | Começar ensaio local pequeno; coletar dados diversos na Etapa 3 |
| Modelo SAM 2 pode exigir recursos computacionais elevados | ⚠️ Hardware/ambiente ainda não verificados | Testar em ambiente isolado; oferecer caminho sem IA/sem GPU |
| Numerações da mesma forma podem ser indistinguíveis na fotografia | ⚠️ Sem escala física calibrada | Mostrar hipóteses; adiar numeração conclusiva |
| Microvazador V02 tem pouco contraste | ⚠️ Não detectado de modo confiável | Não relaxar limiar arbitrariamente; reavaliar na Etapa 6 |
| Fotos/CAD de produção são proprietários | ⚠️ Repositório público | Dados somente em local privado com acesso controlado |
| Tolerâncias industriais | ⬜ Ainda não definidas | Discutir com Qualidade na Etapa 7, após metrologia |

## 7. Rotina de atualização obrigatória deste plano

**Ao começar uma tarefa:**
- Ler este arquivo e escolher a próxima caixa `[ ]` da etapa ativa.
- Marcar como `🚧 em execução` apenas o trabalho de fato iniciado.
- Preservar limites experimentais e documentar qualquer mudança de escopo.

**Ao entregar código:**
- Executar testes de backend e compilação do frontend, conforme necessário.
- Marcar `[x]` **somente** o que foi verificado.
- Registrar evidência: commit, PR, testes, número de fotos/peças e resultados ou "não medido".
- Atualizar **"Onde estamos agora"** (etapa, status, próxima ação) e a data no topo.
- Acrescentar uma entrada em **"Histórico de alterações do plano"**.
- Incluir a atualização deste arquivo no mesmo PR/branch da implementação.

**Se o experimento falhar:** não marcar tarefa como sucesso. Registrar o que falhou, aprendizado, impedimento e alternativa. Decisões de descartar um método também podem encerrar uma etapa, desde que documentadas.

### Histórico de alterações do plano

| Data | Alteração | Status |
|---|---|---|
| 22/10/2026 | Criação do plano mestre na raiz; consolidada base atual e roteiro de IA até operação industrial | Plano inicial — Etapa 1 próxima |
| 23/10/2026 | Contrato único de máscaras v1, baseline OpenCV isolado, rota experimental e testes; E1.1/E1.2 concluídas após CI verde | Etapa 1 em execução |
| 23/10/2026 | E1.3: executor SAM 2 opt-in, sem downloads/dependências novas no serviço padrão, testes de indisponibilidade e predição simulada; CI aprovado | **E1.3 concluída no código** |
| 03/11/2026 | E1.4: painel lado a lado no Vue, acionamento manual, tratamento de indisponibilidade e invalidação de respostas antigas; CI aprovado | **E1.4 concluída no código** |
| 03/11/2026 | E1.5: testes de transporte/contrato e descarte de respostas obsoletas, integrados ao build Vue; 12 novos testes e CI backend/frontend verde | **E1.5 concluída** |
| 03/11/2026 | E1.6: métricas de silhueta humana (IoU/Dice e bordas em px), API/GUI opt-in, indisponibilidade sem pontuação, testes sintéticos e CI aprovado | **ETAPA 1 concluída no código** |
| 03/11/2026 | E2.1: licença/requisitos oficiais, checklists de CPU/GPU e pareamento de checkpoint, preflight sem inferência, bloqueio de variante incompatível e testes aprovados | **E2.1 concluída** |
| 03/11/2026 | E2.2: primeiro diagnóstico do Linux do operador — Python 3.14, SAM 2 desligado, bibliotecas e checkpoint ausentes | **Ambiente local ainda não preparado; E2.2 aberta** |
| 03/11/2026 | Inventário detalhado do hardware (RAM/swap/Ubuntu/GPU não confirmada); instruções verificadas para criar Python 3.12 isolado com `uv` sem alterar Python do sistema | **E2.2 segue em preparação; sem inferência real** |
| 03/11/2026 | E2.2: uv 0.13.7 e Python 3.12.16 confirmados; laboratório isolado criado; 4,5 GiB RAM disponível e swap de 4 GiB praticamente saturada, 31 GiB em disco | **Ambiente criado; aguarda diagnóstico de memória antes de instalar IA; E2.2 aberta** |
| 04/11/2026 | E2.2: RAM disponível 2,5 GiB, swap usada 3,9/4 GiB, processo isolado de conteúdo web ~4,54 GiB RSS; diagnóstico e orientação segura em `docs/SAM2_DIAGNOSTICO_MEMORIA_E2.md` | **Aguardar nova avaliação de recursos; sem instalação de IA** |
| 04/11/2026 | E2.2: segunda coleta — RAM disponível 3,2 GiB, swap utilizada 2,6 GiB, sem paginação contínua nas amostras finais de `vmstat`; processo web principal ~4,53 GiB RSS persiste | **Melhora parcial; solicitar encerramento normal do navegador e reavaliar antes de instalar IA** |
| 04/11/2026 | E2.2: terceira coleta com 9,1 GiB RAM disponível e 1,9 GiB swap ocupada; risco imediato de memória reduzido, instalação CPU-only de PyTorch/TorchVision documentada, não executada | **Na coleta ainda não executada; ver resultado posterior abaixo** |
| 04/11/2026 | E2.2: instalados torch 2.15.0+cpu e torchvision 0.29.2+cpu no laboratório; importação interrompida por Ctrl+C. Documentada proposta de IA sob demanda sem instalação nos computadores dos operadores | **Importação não verificada; arquitetura em decisão; sem SAM 2 real** |
| 04/11/2026 | Pesquisa aplicada de visão industrial com fotografias qualitativas de malha e projetos SAM 2, Anomalib, CVAT, DINOv2, Ultralytics e model serving; proposta de dataset privado, ótica e três tarefas independentes | **Direção proposta documentada; nenhum treinamento nem inferência realizados** |
| 04/11/2026 | Requisitos confirmados: vazadores passantes previstos no CAD, DXFs correspondentes e cabine iluminada com câmera fixa. Documento P0 propõe contraste de luz frontal/contraluz, verificação óptica e revisão física sem expor fotos/CAD proprietários | **Requisitos registrados; captura e testes P0 pendentes** |
| 04/11/2026 | Revisadas capturas e relatório histórico: segmentação externa OpenCV 25,76 ms/960×1280, 15 candidatos versus 3 círculos CAD por referência; 9 referências sem numeração, SAM 2 indisponível, sem referência humana nem IoU/Dice. Cabine já existe; câmera não escolhida/instalada. | **Evidência de protótipo documentada, não validada como detecção física** |

---

**Referências dentro do repositório:** `README.md` (estado e execução do protótipo), `docs/VALIDACAO.md` (matriz de validação), `backend/app/vision.py` (baseline OpenCV), `backend/app/matching.py` e `backend/app/family_matching.py` (correspondência CAD), `backend/app/texture_anomalies.py` (análise óptica exploratória), `docs/SAM2_PREPARACAO_E2.md` e `backend/app/sam2_preflight.py` (verificação SAM 2.1).

**Próximo item obrigatório: realizar ensaio exploratório P0 com fotografia original e DXF correspondentes em armazenamento privado, inspecionar fisicamente e anotar vazadores/recortes; comparar visibilidade e separação da trama em captura disponível. Cabine existe, mas não há câmera fixa instalada; reservar compra/escolha após requisitos ópticos. Depois preparar dataset e baselines; E2.2 SAM 2 ainda não concluída.**
