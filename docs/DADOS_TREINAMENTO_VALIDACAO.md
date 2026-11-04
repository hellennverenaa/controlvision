# Dados, treinamento e validação — ControlVision

**Revisão:** 04/11/2026 · **Status:** protocolo proposto, sem dataset de produção montado nem modelo treinado.

## Referências e rótulos

Cada conjunto privado deve preservar: `peca_fisica_id`, material/trama/cor, lote/sessão, câmera/objetiva, iluminação/exposição, foto original, CAD/revisão, referência de peça/modelo/numeração (ou desconhecida), coordenadas originais e responsável pela revisão.

Anotar **separadamente**:
- Máscara externa do corpo da peça com revisão humana.
- Vazador CAD esperado (`cad_feature_id`, formato/posição); entidade CAD não prova abertura física.
- Estado físico revisado do vazador: aberto, ausente/incompleto, deslocado, não observável — com evidência de inspeção.
- Recortes previstos e regiões extras suspeitas.
- Trama normal, sombras, reflexos, sujeira, ruído e casos inconclusivos.

Um anotador deve poder marcar incerteza. Nunca transformar automaticamente os 15 candidatos visuais antigos em 15 vazadores.

## Coleta e protocolo óptico

A cabine existe, mas a **câmera fixa ainda será escolhida**. Antes disso, realizar experimento exploratório com foto original sem overlay, peça física e DXF correspondente; testar iluminação frontal e contraluz com a mesma peça, quando viável. Contraluz pode iluminar **tanto os furos passantes quanto a trama**. Determinar resolução efetiva do menor vazador por padrão físico conhecido, sem alegar tamanho em mm a partir de foto não calibrada.

A escolha do dispositivo final dependerá das evidências de visibilidade, repetibilidade, distância, campo de visão e resolução. Ver [Protocolo da cabine](CABINE_CAMERA_FIXA_VAZADORES_PROTOCOLO.md).

## Treinamento: três linhas de experimento

1. **Silhueta da peça:** OpenCV atual vs SAM 2 assistido vs modelo supervisionado caso o dataset justifique. Máscaras externas avaliadas por IoU/Dice/erro de borda.
2. **Reconhecimento CAD:** identificar **família/modelo**, ranquear referências e lidar com numeração desconhecida e espelhamento. Sem escala física, não adivinhar numeração. Medir Top-1/Top-k, rejeição de desconhecidas e confusão entre tamanhos.
3. **Microvazadores e recortes:** crops em resolução original; aprender trama normal e aberturas fisicamente confirmadas; comparar análise guiada CAD e busca global com PatchCore/EfficientAD, modelos supervisionados e filtros atuais. Medir recall por furo, alarmes falsos por peça, desempenho por material, dimensão em pixels e iluminação.

**SAM 2 não foi executado com pesos reais** e **PyTorch CPU foi instalado no laboratório isolado, mas a importação foi interrompida**; isso não comprova funcionamento. Nenhum treino aconteceu.

## Partição e avaliação

- Separar treino, validação e teste por **peça física**, lote/sessão (e quando possível material/câmera). Fotos rotacionadas da mesma peça não podem cair nos dois lados.
- Congelar um conjunto de teste inédito; revisar divergências humanas e registrar versão dos rótulos e do CAD.
- Separar falha de captura, falha de reconhecimento, vazador não detectado e alerta falso.
- Avaliar em condições difíceis, incluindo peças claras sobre fundo azul e diferentes orientações.
- Não definir limiares industriais ou medir conformidade em mm sem validação metrológica e requisitos da Qualidade.

## Segurança dos dados

O repositório GitHub é público. Fotos, recortes, máscaras associadas a moldes, DXFs proprietários, modelos treinados com informações sensíveis, credenciais e checkpoints devem ficar **fora do GitHub público**, em armazenamento privado com autorização, controle de acesso e retenção documentada.

## Primeiro entregável verificável (P0)

- [ ] Escolher uma peça física e **DXF de revisão confirmada**.
- [ ] Mapear cada vazador/recorte esperado e revisar o estado físico.
- [ ] Obter originais sob luz disponível (e contraluz quando viável) sem publicar.
- [ ] Criar máscara externa revisada e rótulos de vazadores por pessoa.
- [ ] Comparar OpenCV com essa referência e registrar erros concretos.
- [ ] Verificar se o menor vazador é distinguível da trama.
- [ ] Registrar limites e decisão do próximo modelo a avaliar.

**Três fotos antigas e relatório anterior são indícios do problema, não um dataset de treino.** Consulte [Evidência histórica da lingueta](EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md).


## Registro inicial estruturado P0.1

Foi implementado um **validador de metadados offline** (não detector de furos): [Guia de registro P0](P0_REGISTRO_PRIVADO.md). O exemplo versionado é sintético; nenhuma foto, CAD real, avaliação física ou conjunto de treinamento foi enviado. Esse esquema permite preparar registros privados revisados, mas não substitui anotação de pixels ou comprovação óptica.


## Preparação de recortes para a IA 2 — P0

Existe agora um extrator offline de patches (positivos fisicamente confirmados e negativos humanos revisados), mantendo resolução original sem resize e gravação em pasta privada. [Procedimento e limitações](P0_IA2_RECORTE_REFERENCIAS.md). **Ainda não foi criado um conjunto real nem treinado modelo**. Os exemplos do repositório são sintéticos; não associar automaticamente pontos da interface a uma foto diferente.
