# PLANO DE DESENVOLVIMENTO — ControlVision

> **Documento vivo e fonte principal de acompanhamento do projeto.**  
> Atualizado em: **23/10/2026** · Versão do plano: **1.1**  
> Branch de trabalho: `feat/prototipo-validacao` · Estado: **PROTÓTIPO EXPERIMENTAL — NÃO LIBERA PRODUÇÃO**
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

**Fase atual: ETAPA 1 — contrato de segmentação v1 implementado; preparar inferência de IA isolada.**  
**Próxima ação concreta: E1.3** — integrar um executor de IA **opcional e isolado** com indisponibilidade controlada quando bibliotecas/modelos/pesos não estiverem instalados. Não ativar SAM 2 por padrão nem substituir o OpenCV.

| Etapa | Tema | Estado | Condição para avançar |
|---|---|---|---|
| 0 | Base existente do ControlVision | ✅ Base implementada, **não homologada** | Testes de regressão existentes preservados |
| 1 | Preparação para IA + baseline do OpenCV | 🚧 **EM EXECUÇÃO (E1.1 e E1.2 verificadas)** | Comparação reproduzível definida |
| 2 | Testar SAM 2 pré-treinado | ⬜ Pendente | Avaliação documentada contra OpenCV |
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
- [ ] E1.3 Criar módulo experimental isolado no backend para executar inferência de IA, com falha controlada quando modelo/pesos não estiverem instalados.
- [ ] E1.4 Preparar visualização **lado a lado** da máscara OpenCV × máscara IA (sem substituir a referência automaticamente).
- [ ] E1.5 Criar testes sintéticos de contrato, integração, ausência de pesos e regressão.
- [ ] E1.6 Definir protocolo simples de comparação: IoU, Dice, erro de borda, tempo por imagem e falhas de segmentação.

**Entregável:** aplicação atual preservada + interface/API para ensaio comparativo, inicialmente sem promessas de melhor desempenho.

**Parcial em 23/10/2026:** E1.1 e E1.2 implementadas/testadas. `POST /api/vision/segmentation/preview` disponibiliza baseline de silhueta **externa** em máscara PNG/base64 (`schema_version=1.0`, `method=opencv_baseline`); `method=sam2` ainda retorna **422**, sem execução de IA. O baseline preenche o polígono aproximado já emitido pelo OpenCV, não é a máscara bruta original e não identifica vazadores. Fonte: `docs/SEGMENTACAO_CONTRATO.md`. **E1.5 ainda pendente**: os testes atuais cobrem contrato, rota e regressão; faltam casos de modelo/pesos ausentes após E1.3. Máscaras humanas comparativas, métricas reais e testes com fotografias reais: **não medidos**.

**Para encerrar:** testes passando e comparação reproduzível; nenhum aumento não explicado de falhas no fluxo atual.

### ETAPA 2 — Avaliar SAM 2 pré-treinado (sem treinar do zero)

**Meta:** descobrir se um modelo existente já melhora a extração do contorno da peça.

- [ ] E2.1 Verificar licença dos pesos, dependências, requisitos de CPU/GPU e custo de execução.
- [ ] E2.2 Executar SAM 2 de maneira **opcional** em ambiente local de experimento, sem iniciar automaticamente no servidor principal.
- [ ] E2.3 Usar caixa da peça/indicações vindas do OpenCV ou cliques do operador como *prompts*, documentando o nível de intervenção humana.
- [ ] E2.4 Comparar máscara SAM 2 com OpenCV **nas mesmas fotos**, contra máscaras corrigidas por pessoa.
- [ ] E2.5 Registrar casos bons e ruins: fundo azul, tecido claro, malha, rotações, sombras, recortes próximos à borda.
- [ ] E2.6 Decidir: **adotar como auxiliar**, **usar só para anotar dados** ou **não utilizar**.

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
| 23/10/2026 | Segmentação v1, só OpenCV | Máscara PNG/base64 com dimensões, contorno, método, tempo e avisos; endpoint opcional | Backend e frontend aprovados no GitHub Actions; **nenhuma imagem real testada**; **nenhuma IA executada** | [CI](https://github.com/hellennverenaa/controlvision/actions/runs/39945290274); `backend/tests/test_segmentation_contract.py`; **próxima: E1.3** |

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
| 23/10/2026 | Contrato único de máscaras v1, baseline OpenCV isolado, rota experimental e testes; E1.1/E1.2 concluídas após CI verde | Etapa 1 em execução; E1.3 próxima |

---

**Referências dentro do repositório:** `README.md` (estado e execução do protótipo), `docs/VALIDACAO.md` (matriz de validação), `backend/app/vision.py` (baseline OpenCV), `backend/app/matching.py` e `backend/app/family_matching.py` (correspondência CAD), `backend/app/texture_anomalies.py` (análise óptica exploratória).

**Próximo item obrigatório: E1.3 — executor opcional de IA com falha controlada quando não instalado.**
