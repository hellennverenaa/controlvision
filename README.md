# ControlVision

**Protótipo experimental de inspeção geométrica de peças cortadas. NÃO HOMOLOGADO para liberar produção.**

Sistema web que importa DXF e HPGL/PLT, identifica peças candidatas e seus contornos internos, permite selecionar uma peça pela lista ou clicando no desenho e analisa experimentalmente fotografias ou webcam. A classificação interna pode ser revista pelo operador.

## Tecnologias

- Vue 3 + TypeScript + Vite no frontend.
- Python + FastAPI, ezdxf, Shapely e OpenCV no backend.
- PostgreSQL, auth corporativa, PM2 e API Gateway: integrações posteriores, após validação.

## Executar localmente

### Atalhos Linux para o dia a dia

Depois da instalação inicial, abra **dois terminais**, ambos na raiz do projeto:

    cd ~/Documentos/ambiente_dass/controlvision
    npm run backend

    # Em outro terminal, na mesma pasta:
    cd ~/Documentos/ambiente_dass/controlvision
    npm run frontend

O script `npm run backend` utiliza o Python do próprio `backend/.venv`, inicia FastAPI/Uvicorn na porta 8000 e dispensa `source .venv/bin/activate`. O comando `npm run frontend` chama o Vite em `frontend`. Para interromper, use Ctrl+C em cada terminal.

Se a pasta `backend/.venv` ainda não existir, faça uma única instalação:

    cd backend
    python3 -m venv .venv
    .venv/bin/python -m pip install -r requirements.txt
    cd ..

Esses atalhos usam Bash e foram destinados ao desenvolvimento Linux local. Não configuram PostgreSQL, autenticação, PM2 ou infraestrutura corporativa.

### Comandos manuais (também funcionam)

Backend (Python 3.11 ou superior):

    cd backend
    python -m venv .venv
    # Linux: source .venv/bin/activate
    # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Frontend (Node 20+):

    cd frontend
    npm install
    npm run dev

Abrir http://localhost:5173; Vite encaminha chamadas /api ao FastAPI local.

Testes automatizados:

    cd backend
    pip install pytest
    python -m pytest -q

## Roteiro de validação

1. Importar um DXF com uma peça e outro com várias peças e numerações.
2. Confirmar cada contorno no desenho e na lista de seleção.
3. Verificar círculos e recortes internos; marcar provisoriamente como vazador, referência ou ignorar.
4. Importar o HPGL equivalente e observar diferenças de agrupamento.
5. Enviar uma imagem ou usar a webcam apenas para inspecionar a extração visual de contorno.


## Fluxo guiado de teste (atualização)

1. **Importar CAD** e escolher uma peça pela lista ou pelo desenho.
2. **Conferir geometrias internas.** O programa destaca círculos com marcadores maiores, apenas para visualização. Um círculo interno recebe a sugestão de "possível vazador", mas a função precisa ser confirmada por alguém que conheça o molde.
3. **Testar imagem.** Envie uma fotografia ou use a webcam, de preferência com uma peça realmente recortada, plana e em fundo contrastante. O contorno vermelho é somente o contorno detectado em pixels.
4. **Comparação dimensional CAD x peça** ainda está indisponível: faltam alinhamento rígido, calibração, medição dos vazadores e testes metrológicos.

Uma fotografia de **um contorno desenhado com caneta sobre uma folha de papel** não permite testar a identificação dos vazadores físicos, já que eles não estão recortados. Os contornos brutos encontrados pela segmentação incluem ruídos e não indicam quantidade de defeitos.

Os dados de classificação da etapa 2 não são gravados, e a confirmação visual não autoriza uso industrial.

## Etapas navegáveis e análise interna de imagem

A interface agora separa as etapas em telas reais: **1 — Importar CAD**, **2 — Conferir candidatos internos**, **3 — Analisar fotografia**. As três primeiras etapas são clicáveis na navegação superior quando o CAD correspondente foi selecionado. Depois de confirmar os círculos no CAD, pressione **Continuar para Etapa 3**.

Na Etapa 3 selecione o tipo de imagem:
- **Desenho no papel:** procura pontos escuros aproximadamente circulares, mas não afirma que sejam vazadores físicos.
- **Peça recortada com contraste:** procura pequenas aberturas claras no interior de uma região escura, preferencialmente com iluminação traseira.

Os candidatos aparecem com contornos amarelos sobre a fotografia. O número de candidatos da foto e os vazadores confirmados no CAD são mostrados separadamente. **Igualdade de contagens não comprova posição, dimensão ou conformidade**. Ainda não há alinhamento CAD-fotografia nem medição em mm.

Testes automatizados usam fotografias sintéticas: seis marcas sobre papel, seis aberturas sobre peça escura e ausência de furos. As condições reais podem gerar falsos negativos ou falsos positivos.

## Prévia de correspondência CAD × imagem (experimental)

Depois de confirmar as geometrias internas no CAD e abrir a Etapa 3, a API tenta sobrepor o contorno CAD à silhueta identificada na imagem e relacionar os centros dos vazadores confirmados com os pontos detectados na foto.

- O contorno **azul tracejado** é uma projeção ilustrativa do CAD sobre a foto; o contorno **vermelho** é a detecção da foto; os círculos **amarelos** são candidatos da imagem; as linhas **verdes** indicam associações sugeridas.
- Pontos esperados sem candidato e candidatos sem associação são apresentados separadamente. Isso **não indica furo ausente ou defeito**: a segmentação pode confundir rabiscos, sombras ou perspectiva.
- O algoritmo utiliza rotação e translação e um **fator de escala calculado das áreas das silhuetas exclusivamente para visualização**. Não redimensiona o molde original nem fornece calibração metrológica. **Não usar o alinhamento automático para esconder diferenças dimensionais**.
- Quando o alinhamento da silhueta tem qualidade baixa, associações automáticas são bloqueadas. O sistema ainda mostra a prévia e recomenda uma imagem melhor.
- O algoritmo não corrige perspectiva nem espelha automaticamente a peça. A comparação dimensional em milímetros continua indisponível.

Testes sintéticos cobrem diferentes rotações, um candidato extra e um vazador CAD não encontrado na fotografia. Necessitamos de ensaio real com peça correspondente ao DXF antes de declarar a correspondência validada.

## Teste com várias numerações e peça sem tamanho conhecido

Se o arquivo DXF ou HPGL contiver **mais de uma peça**, o sistema não escolhe automaticamente a primeira. Na Etapa 2, o operador pode selecionar **Não sei a numeração** para continuar sem definir um tamanho. Nesse modo, a Etapa 3 analisa somente a fotografia: **nenhuma geometria CAD é enviada à correspondência**. A plataforma não pode inferir o tamanho real em milímetros de uma imagem sem calibração, mesmo que os moldes tenham formas semelhantes.

Na fotografia, escolha **Peça física cortada** e depois o contraste esperado: **peça escura/fundo claro** ou **peça clara/fundo mais escuro**. Se o algoritmo selecionar praticamente o fundo inteiro, tocar as bordas da captura ou selecionar uma região improvável, exibirá **Captura inconclusiva**, sem lista de vazadores nem sobreposição CAD. Este bloqueio é heurístico e não detecta todas as falhas possíveis.

Um único arquivo com todas as numerações já é suficiente para nossos testes de **importação e seleção visual**. Identificação automática de numeração, máscara interativa/ROI e medição dimensional ficam para validação posterior. Não é necessário comprar câmera, medir a peça com régua ou configurar PostgreSQL agora.

## Peça real clara sobre tecido azul e limite da análise percentual

**Novo ensaio experimental:** a imagem de uma peça clara apoiada em tecido azul mostrou que a rotina anterior identificava parte do tecido como peça e devolvia falsos vazadores. No modo "Peça física" + "Peça clara, fundo mais escuro", o protótipo agora tenta isolar o material com características de cor (saturação baixa e luminosidade alta). Essa regra é específica e **não é garantida para todas as cores e texturas**.

Os furos observados são muito pequenos para a resolução da imagem reduzida usada no ensaio. Mesmo com contorno externo identificado, os círculos internos podem não ser resolvidos: **zero candidatos na foto não comprova zero furos presentes**. É necessário preservar a resolução original da captura e, futuramente, validar óptica, iluminação e repetibilidade.

### O que significa o percentual mostrado

Quando uma referência CAD **específica** é selecionada e o ajuste visual da foto tem qualidade suficiente, a tela pode apresentar um **percentual experimental de diferença de forma**. O cálculo é 100 × (1 − área da interseção / área da união) das duas silhuetas após *normalização ilustrativa de escala e rotação*.

Este percentual **NÃO é percentual de erro de corte, nem medida em mm, nem critério de aprovação**. O ajuste ilustrativo pode esconder diferenças uniformes de tamanho. Se a numeração for desconhecida, a captura inconclusiva ou o alinhamento for ruim, não há percentual confiável a exibir. Rotações da peça no plano não são tratadas como defeitos.

A futura medição dimensional precisará da numeração/escala correta, calibração em mm no plano físico, controle de perspectiva e correspondência rígida sem redimensionar a referência para minimizar desvios.

## Revisão manual de vazadores microscópicos (experimental)

No teste de uma peça clara sobre tecido azul, o sistema identificou o contorno externo, mas retornou **0 vazadores automáticos**. Esse resultado significa apenas que a imagem não apresentou candidatos reconhecidos pelos filtros atuais; **não é evidência de ausência de furos**.

Na **Etapa 3**, ao carregar ou capturar a fotografia, use **Ampliar fotografia** para revisar o material na maior área de tela disponível. Se conseguir distinguir visualmente os pontos, clique em **Marcar furinhos manualmente** e depois sobre cada posição na fotografia. O sistema desenhará marcadores **roxos**, separados dos candidatos **amarelos** detectados automaticamente. É possível desfazer/limpar essas anotações; as coordenadas são indicadas em pixels de imagem.

As marcações são provisórias, não são gravadas no banco e **não entram na correspondência geométrica nem alteram as contagens automáticas**. Servem para identificar onde o algoritmo não conseguiu detectar um possível furo, antes de estudar detecção melhor e câmeras de maior resolução. Ampliar digitalmente não aumenta detalhe óptico.

Se a numeração ainda é desconhecida, a interface informa por que não compara com um tamanho CAD selecionado ao acaso.

## Inspeção assistida de furinhos muito pequenos

Se o modo de peça física mostra **0 candidatos**, mas alguém vê furinhos, continue usando **Marcar furinhos manualmente** na Etapa 3 e em seguida clique **Analisar regiões marcadas**.

A API `POST /api/vision/manual-regions` recebe a **fotografia original** (não a captura de tela), o tom da peça e as coordenadas inseridas pelo operador. Para cada ponto, examina brilho e saturação dentro da peça, compara com a vizinhança e indica **Contraste observado** ou **Inconclusivo**.

**Atenção:** essas marcações são humanas, não detecções automáticas. Contraste também pode ser sujeira, pigmento, trama ou sombra. O relatório não confirma furos passantes, não compara o CAD e não avalia defeito. Um ponto inconclusivo **não significa furo ausente**. O fluxo é um instrumento de diagnóstico para melhorar depois o detector automático com material de teste real.

Este teste é especialmente importante perto das bordas da peça, onde antigos filtros por área e raio mínimo rejeitavam pequenos furos.

## Busca assistida em torno das marcações

Depois do teste real com três marcações, foi observado contraste de intensidade de aproximadamente -1,5, 44 e 18 níveis exatamente sobre os cliques. Isso não permite confirmar furos.

Na análise assistida, o sistema também pesquisa **pequenos sinais ópticos em um raio máximo de 11 pixels em torno de cada marcação**. Reporta localização sugerida, deslocamento e força do sinal local, separando-o do contraste medido no clique original. O algoritmo só procura locais situados dentro do contorno detectado; ainda pode destacar sujeira, textura, sombras e artefatos. Um sinal encontrado **NÃO confirma a existência de um vazador** e um sinal não encontrado **NÃO comprova sua ausência**.

Esses sinais são usados apenas para diagnosticar falhas de detecção dos vazadores minúsculos. Não são associados automaticamente a uma numeração CAD, não são contabilizados como detecção automática e não alteram percentuais, medidas ou aceitação de peças. Nenhum dado de imagem proprietária está versionado neste repositório público.

## Detecção automática exploratória de micropontos

O detector de furos físicos possui **dois caminhos distintos** para peças claras sobre fundo contrastante:

- **Círculos (amarelo):** contornos fechados detectados pela segmentação convencional.
- **Micropontos (ciano):** componentes muito pequenos encontrados por diferença local entre imagem suavizada e fundo estimado, sem marcações manuais. A busca é limitada ao interior da silhueta (com margem de segurança), exige contraste acima do ruído e evita duplicar círculos já detectados.
- **Pontos roxos:** posições fornecidas manualmente pelo operador, sem contar como detecção automática.

**Aviso:** um microponto ciano pode ser furo real, sombra, mancha, fibra ou artefato da câmera. Não equivale a vazador confirmado, nem é usado na correspondência CAD ou na decisão de qualidade. O algoritmo pode deixar de encontrar furos de baixa resolução ou sugerir micropontos falsos. Os limiares são experimentais e ainda não foram validados com amostras reais rotuladas.

O teste sintético verifica detecção de pontos de aproximadamente 1–2 pixels, superfícies lisas, ruído leve, pontos externos e ausência de duplicações. A fotografia enviada na conversa é uma captura de tela e não foi incorporada ao repositório público. Precisamos repetir com imagem original da câmera e conferir cada sugestão visual.

## Resultado do teste em várias rotações (20/10/2026)

Quatro capturas de uma mesma peça clara sobre tecido azul, em orientações diferentes, mostraram que a **segmentação do contorno externo permanece funcional**, mas a detecção óptica dos vazadores **não é repetível**:

- Captura vertical: um candidato circular amarelo perto da borda, sem micropontos cianos.
- Captura inclinada: três grupos de micropontos cianos.
- Outra captura vertical: três grupos de micropontos cianos.
- Captura inclinada com textura mais aparente: dezenas de micropontos cianos, com numerosos falsos candidatos.

**Conclusão:** três candidatos em uma única imagem não equivalem a três vazadores verificados. A forte dependência da orientação/iluminação e da textura do material bloqueia a validação da detecção automática nesta etapa.

O protótipo agora apresenta **"Detecção instável: excesso de sinais compatível com textura"** se houver muitos micropontos distribuídos pela área detectada. Nesse cenário, os marcadores cianos ficam inicialmente ocultos e podem ser revelados apenas para diagnóstico. A decisão é uma heurística de triagem, não uma regra universal; peças legítimas com muitos vazadores também poderão produzir um alerta, que deverá ser revisado.

Para evoluir a técnica precisamos dos **arquivos originais das fotografias**, sem sobreposição vermelha, amarela ou ciana gerada pelo ControlVision. Capturas de tela com os overlays são ótimas para entender a interface, mas inadequadas para aferir rigorosamente o detector. As fotos proprietárias não devem ser enviadas ao repositório público sem autorização.

## Validação das cinco fotografias sem overlays (20/10/2026)

Recebemos cinco imagens da mesma peça clara em diferentes orientações, cada uma com **525 × 300 pixels**, sem as marcações desenhadas pela aplicação. O ensaio local do algoritmo anterior revelou dois problemas:

- A máscara de peça clara por HSV podia escolher **piso/superfície clara conectada à borda** como componente externo e descartar a peça por ela aparecer aninhada na hierarquia de contornos (4 de 5 imagens do conjunto reproduziram o problema).
- Quando a seleção ignora a profundidade da hierarquia, mas continua exigindo que o candidato não toque as margens e tenha área plausível, a **silhueta principal foi recuperada nas cinco imagens** desse teste local.
- O detector de micropontos anterior **não recuperou os três sinais de forma estável nesses arquivos de 525 × 300 px**. Isso não contradiz resultados anteriores com capturas de maior resolução: são entradas diferentes.
- Portanto, **não se deve reduzir indiscriminadamente os limiares para aumentar artificialmente a contagem**. A aplicação mostra aviso quando a imagem possui menos de 0,5 megapixel; essa faixa é um limiar experimental de alerta, não um requisito metrológico validado.

O código foi corrigido para permitir que uma peça clara seja um contorno aninhado na imagem sem confundir a mesa clara conectada às bordas com a peça. Foram acrescentados testes sintéticos de fundo azul e margens brancas. Fotos reais não foram versionadas no repositório público.

## Anotações versus detecção automática (revisão experimental)

Em uma fotografia de teste, o operador anotou três posições (M01/M02/M03) e o detector indicou 23 candidatos circulares. A comparação por proximidade em pixels revelou **uma coincidência de aproximadamente 1 px (M03 ↔ I02)**; os candidatos mais próximos de M01 e M02 estavam a aproximadamente 479 e 485 px, respectivamente. Isso demonstra que acertar a contagem de candidatos isoladamente não comprova detecção correta.

Após marcar pontos e clicar **Analisar regiões marcadas**, o relatório inclui uma **associação espacial um-para-um**, em raio experimental de 12 px, mostrando: candidato automático próximo de cada marcação, distância, marcações sem associação e candidatos não associados. Inclui tanto círculos clássicos como micropontos, mantendo seus tipos separados.

O raio de 12 px serve apenas para comparar coordenadas de imagens e cliques. **Não é tolerância dimensional, nem prova de furo físico**, e uma anotação pode estar deslocada. Candidatos sem anotação não são necessariamente falsos positivos.

Se todas as peças do arquivo CAD apresentam a mesma contagem de geometrias circulares e a fotografia oferece candidatos em quantidade muito superior (critério provisório: pelo menos 10 e 3 vezes o número CAD), a interface exibe alerta de **possível influência da textura**. Não deduz defeitos nem altera os resultados brutos.

O estudo seguinte será restringir a busca de sinais à vizinhança das geometrias CAD projetadas para várias numerações, com revisão e sem determinação artificial de escala métrica.

## Prévia de padrão CAD com numeração desconhecida

Se o CAD contiver vários tamanhos e o operador selecionar **Não sei a numeração**, o backend pode avaliar **até 15 geometrias** como hipóteses de posição do contorno e das geometrias circulares internas. A Etapa 3 mostra as referências avaliadas e permite selecionar **uma referência apenas para visualização**, desenhando seus centros previstos com círculos azuis tracejados. Amarelo = círculo detectado na foto; ciano = microcontraste; roxo = anotação humana.

Cada referência usa um fator de escala extraído da área das silhuetas **apenas para a projeção ilustrativa na fotografia**. Essa escala elimina as diferenças absolutas entre numerações: portanto, a comparação **não identifica tamanho, não mede corte, não calcula erro dimensional, nem determina conformidade**. Vários tamanhos podem parecer igualmente compatíveis. O sistema não altera o CAD original nem escolhe a numeração.

Há um controle específico de quantos candidatos visuais estão próximos às posições projetadas, mas **proximidade não confirma vazador**; a malha pode produzir pequenos falsos sinais próximos por acaso. Sobreposições com ajuste de contorno baixo não devem ser usadas. É imprescindível validar esse caminho com peças físicas e referência verificada antes de qualquer conclusão industrial.

## Teste visual CAD × foto com tamanho ainda desconhecido

Na prévia da família CAD, o sistema apresenta agora **o contorno CAD em azul tracejado**, junto dos três centros CAD também azuis. O contorno **vermelho** continua sendo a silhueta segmentada da fotografia; os círculos **amarelos** são candidatos ópticos e não vazadores confirmados.

Confira primeiro se o contorno azul realmente acompanha o vermelho. Se não acompanhar, o deslocamento dos centros azuis pode ser **erro de alinhamento**, e não problema com os vazadores da peça. Só depois examine as coincidências dos pontos. A interface também mostra a qualidade experimental do ajuste.

A transformação utiliza escala **normalizada para visualização**, rotação e translação. Não representa medição dimensional e **não escolhe automaticamente a numeração**. Esta mudança melhora o diagnóstico da sobreposição, mas não declara o detector de vazadores validado.

## Limites conhecidos

- Nenhuma aprovação/reprovação automática de produção.
- Sem calibração óptica nem comparação CAD x fotografia em milímetros.
- Sem tolerâncias definidas ou metrologia validada.
- O importador pode gerar candidatos falsos. Todos devem ser revisados.
- Camadas do DXF não são usadas como classificação definitiva de contorno e furo.
- DXFs podem não declarar unidade de medida; a escala HPGL usada é hipótese de 40 unidades/mm.
- O upload não persiste no servidor; classificações não persistem após recarregar a página.
- Os CADs reais da fábrica NÃO foram colocados no repositório público.
- Limite experimental de 20 MB por CAD e 15 MB por fotografia.

Consulte docs/VALIDACAO.md.

## Crédito / licenças

Implementação nova; o projeto SeAMKedu/dxf_contour_comparer foi consultado como referência, mas não teve seu código copiado por ausência de licença explícita. Respeitar licenças das dependências.
