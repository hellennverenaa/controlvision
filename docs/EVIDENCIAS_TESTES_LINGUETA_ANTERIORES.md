# Evidências anteriores — lingueta em malha, OpenCV e correspondência CAD

**Registro:** 04/11/2026. **Origem:** duas capturas de tela e texto de relatório fornecidos pelo operador, gerados em ensaios anteriores. **Status:** evidência histórica de protótipo, não teste novo executado neste registro. Capturas, fotografias e moldes **não foram versionados neste repositório público**.

## Estado da instalação física

A **cabine de inspeção já existe**, mas **a câmera ainda não foi instalada ou escolhida**. A escolha de câmera foi adiada para fase posterior. Fotografias históricas podem ser utilizadas em experimentos exploratórios, sem alegar equivalência a um sistema de captura final estabilizado.

## Evidência recebida

- Fotografia de lingueta clara em malha sobre fundo azul; captura com visualização de contorno exterior e candidatos internos.
- O laboratório OpenCV segmentou a **silhueta externa preenchida**: `status=ok`, **25,76 ms**, resolução **960 × 1280 px**. Esse tempo é só processamento informado pela UI, não latência ponta a ponta, e não é medida de precisão. Não houve referência humana revisada para IoU/Dice.
- SAM 2: **indisponível/desativado**, tempo indicado **0,02 ms**. Isto não é inferência de IA.
- Detector global: **15 candidatos circulares** amarelos; o relatório alerta excesso diante dos **3 círculos internos de cada referência CAD**, potencial confusão com a trama. `0` micropontos automáticos, `0` marcações humanas e **0 confirmações físicas** no registro; nenhum desses números demonstra ausência/presença real dos vazadores.
- **9 referências CAD avaliadas**, sem numeração identificada; escala normalizada para visualização. Em uma referência ilustrativa, **2 de 3 geometrias circulares** apresentaram algum candidato próximo. Este indicador não valida furos.
- Alinhamento por silhueta: qualidade preliminar; refino com **31 px de translação** e **1,23° de rotação** (sem escala adicional no refino). Diferença visual das silhuetas sobrepostas: **1,6%**, que **não equivale a desvio dimensional nem erro de corte**.
- Inspeção em centros projetados: `V01` e `V03` rotulados **sinal suspeito**; `V02` **inconclusivo**. Resultados ópticos não confirmam abertura nem ausência:
  - `V01`: 1 pico acima do limiar, contraste 80 vs 68,1 níveis, pico a 3,3 px do centro CAD; comparação com trama local p90 de 56 níveis e destaque de +24 níveis.
  - `V03`: 1 pico, contraste 99 vs 97,8 níveis, a 9,2 px do centro; trama p90 58 níveis e destaque +20.
  - `V02`: 0 picos acima do limiar, máximo 60 vs limiar 76,5 níveis, pico bruto a 11,6 px; trama p90 62 níveis, destaque de −14.
- Pesquisa multiescala de contraste irregular `5/9/15 px`: `V01` mostrou contraste irregular incomum; `V03` e `V02` ficaram sem destaque perante a trama. Isso **não verifica fisicamente** qualquer perfuração.
- A tela de avaliação E1.6 confirma: **nenhuma máscara humana revisada foi fornecida**, portanto métricas de máscara (**IoU, Dice, distâncias de borda**) **não medidas**.

## Interpretação e limitações

**É correto afirmar que** o baseline OpenCV separou visualmente a silhueta do fundo azul nesta captura e que a detecção global produziu mais candidatos que as geometrias circulares do CAD. **Não é correto concluir** que detectou 2 vazadores reais, que faltou V02, que a peça está conforme/não conforme ou que o erro geométrico é 1,6%.

O erro mais relevante é a confusão entre **trama normal** e **furos passantes de corte**. A calibração e a referência física verificadas continuam ausentes. A diferença de orientação nas fotografias anteriores reforça a necessidade de reconhecer sem assumir numeração.

## Próximo experimento sem escolher a câmera final

1. Obter em ambiente **privado** o DXF exato da peça e identificar com revisão humana os vazadores/recortes que são operações de corte (não apenas círculos).
2. Registrar a verificação física de cada furo esperado (aberto/incompleto/ausente/incerto) e eventuais aberturas extras; preferir anotar as imagens originais, não o overlay.
3. Criar máscara binária externa revisada para comparar com OpenCV na funcionalidade E1.6 (não usar máscara gerada por OpenCV como ground truth).
4. Capturar a mesma peça em iluminação frontal e, se possível, luz transmitida, sem mudar posição da peça, para determinar visibilidade de microvazadores face à malha.
5. Medir qualidade de captura e resolução óptica com alvo conhecido, antes de comprar ou escolher câmera; diferenciar testes exploratórios com celular dos ensaios finais na cabine.
6. Treinar e avaliar identificação da referência CAD e microvazadores **separadamente**, com divisões por peça física e rótulos revisados. Nenhum resultado nesta evidência autoriza aprovação/reprovação industrial.

## Arquivos relacionados

- [Protocolo da cabine](CABINE_CAMERA_FIXA_VAZADORES_PROTOCOLO.md)
- [Pesquisa de IA para trama e CAD](PESQUISA_IA_INSPECAO_TRAMAS_CAD_2026-11-04.md)
- [Plano mestre](../PLANO_DESENVOLVIMENTO.md)

**Registro documental apenas; não foram executados testes, treinamentos ou inferência adicionais.**


## Nova rodada visual com duas orientações — 04/11/2026

**Origem:** quatro capturas de tela fornecidas pelo operador e relatório textual do laboratório de imagem; fotografias e overlays **não adicionados ao GitHub**. Não foi fornecida uma anotação física individual dos três furos nem referência de máscara humana.

**Captura A, lingueta rotacionada:** visualização da foto e máscara OpenCV externa preenchida, com `status=ok`, **23,7 ms**, **960 × 1280 px**. SAM 2 `indisponivel` (**0,01 ms**, sem inferência). Uma captura de overlay mostra **100 candidatos circulares amarelos** concentrados numa região da malha, comparados às **três entidades circulares previstas** por referência CAD. Relatório da mesma rodada apresenta **0 de 3 candidatos próximos** dos centros na referência ilustrativa; **9 referências** continuam sem numeração identificada. Ajuste adicional: **22,7 px de translação e −0,47° de rotação** usando somente contorno externo; diferença visual normalizada **1,7%**, sem significado metrológico.

**Contraste localizado CAD, captura A:** V01/V02/V03 recebem etiqueta de **sinal suspeito**, mas picos estão apenas marginalmente acima dos limiares (**+0,9 / +0,3 / 0 níveis**, respectivamente). O relatório compara os sinais à trama: V01 ficou **+5 níveis** vs p90 local, V02 **−8**, V03 **+25**. Em análise multiescala, V01 e V03 apresentam alteração incomum em 15 px; V02 não se destaca da trama. **Nenhum desses resultados demonstra furo detectado ou ausente**. O relatório registra **0/0 marcações humanas confirmadas**.

**Captura B, outra orientação:** OpenCV `status=ok`, **21,08 ms**, **960 × 1280 px**; SAM 2 `indisponivel` (**0,01 ms**). Máscara externa visualmente acompanha a silhueta. Captura de overlay de outro teste mostra **15 candidatos amarelos**, também mais que as três entidades circulares por CAD. **Não houve máscara de referência humana e não há IoU/Dice**.

**Conclusão técnica da rodada:** o baseline mantém aparência visual coerente de segmentação externa em orientações distintas, mas a etapa de sinais internos **não é robusta**: grande variação de candidatos (15 vs 100) para fotos/malhas e `0/3` nas proximidades ilustrativas é incompatível com qualquer alegação de identificação confiável. A mudança de contagens não pode ser atribuída somente à orientação: as capturas podem ser fotografias, regiões e parâmetros diferentes. O indicador `0/3` **não é taxa de recuperação física**, e a numeração continua desconhecida.

**Próximo experimento controlado:** usar a **mesma fotografia original F01**, mesma configuração/modo e uma referência CAD escolhida explicitamente **somente para registro visual**; marcar manualmente os três vazadores efetivamente identificados por inspeção física (em correspondência com suas posições no CAD, sem presumir numeração), confirmar cada um e comparar distâncias em **pixels** entre pontos roxos e centros azuis. Repetir com uma segunda orientação somente após estabelecer referência e registrar configuração; manter avaliação óptica e contagem global separadas. Não ajustar limiar para forçar `3` candidatos, nem comparar tempos como benchmark industrial.


## Validação humana anotada na interface — 04/11/2026

**Nova evidência do operador:** sobreposição visual com **três pontos humanos roxos**, declarados como **3 de 3 fisicamente confirmados** na interface: M01 (825,6; 590,8) px, M02 (823,7; 719,5) px e M03 (240,5; 634,2) px. A declaração do operador é a referência experimental disponível; **não houve aferição metrológica independente**, nem vinculação comprovada ao manifesto privado.

A comparação de candidatos automáticos retornou **2/3 marcações com candidato a até 12 px**: M01→I08 a 2 px, M03→I04 a 4,5 px; M02 **sem candidato próximo** (o mais próximo a 127 px). **Recuperação experimental por proximidade de 66,7% nesta única fotografia**; 13 candidatos automáticos não associados e não revisados, **não necessariamente falsos positivos**. Há 15 candidatos circulares no total, 0 micropontos e nove referências CAD comparadas sem seleção confiável de numeração.

O cruzamento manual com os centros CAD projetados apresentou **M01→V01 a 1,6 px**, **M02→V02 a 1,6 px**, **M03→V03 a 5,1 px**. Os três pontos ficam dentro das regiões de investigação projetadas (raio 17 px); o problema de M02 está no detector/contraste, não em ficar fora da ROI ilustrativa. Isso é **somente distância de tela em pixels com escala de visualização normalizada**, não valida a numeração, o corte nem dimensões em mm.

Diagnóstico local por marcação: M01 apresentou contraste observado no clique (73 níveis), M02 contraste 0,5 e foi inconclusivo, M03 contraste −14,5 e também foi inconclusivo; a associação por candidato global com M03, portanto, **não prova contraste suficiente no clique nem confirmação por IA**. SAM 2 continuou indisponível; sem máscara externa humana para IoU/Dice. **Conclusão:** posicionamento da projeção CAD é útil para conduzir análise, mas a detecção de microvazadores continua vulnerável à textura; priorizar avaliação com referências físicas e patches de alta resolução.

**Nenhuma foto, máscara ou arquivo CAD proprietário foi adicionado ao repositório por esta atualização.**
