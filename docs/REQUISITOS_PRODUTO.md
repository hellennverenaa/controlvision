# ControlVision — visão do produto e requisitos

**Última revisão:** 04/11/2026 · **Estado:** requisitos de negócio confirmados e requisitos de implementação propostos. Protótipo não homologado.

## 1. Problema e objetivo

A fábrica corta peças de calçados utilizando arquivos **CAD/DXF**. Algumas peças contêm **vazadores: pequenos furos passantes que devem ser executados pela máquina de corte conforme o CAD**. Máquinas podem cortar incorretamente, não abrir furos, fazê-los incompletos/deslocados ou gerar aberturas e recortes indevidos. A trama natural dos materiais, com diferentes cores, malhas e texturas, pode parecer uma coleção de pequenos furos na fotografia.

**Meta:** o operador posiciona a peça na cabine; o ControlVision encontra referências CAD compatíveis, investiga cada vazador e recorte esperado e pesquisa sinais adicionais, retornando evidências e regiões inconclusivas para revisão. A interpretação visual da IA não substitui a comprovação física nem a metrologia.

## 2. Requisitos confirmados pelo responsável pelo projeto

| Código | Requisito | Estado |
|---|---|---|
| RF-01 | Sistema **web online** acessível por vários computadores da produção | Confirmado como destino, não implantado |
| RF-02 | **Cabine física já existe**, iluminação abundante | Confirmado |
| RF-03 | **Câmera será fixa**; modelo ainda **não escolhido nem instalado**; escolha reservada para etapa posterior | Confirmado |
| RF-04 | Arquivos CAD correspondentes, com posições de vazadores/recortes, estão disponíveis | Confirmado; arquivos reais não são públicos |
| RF-05 | Vazadores são **furos passantes minúsculos**, previstos no CAD | Confirmado |
| RF-06 | Materiais apresentam cores e tramas que geram falsos candidatos ópticos | Confirmado e observado qualitativamente |
| RF-07 | Identificar referência de peça/modelo/numeração, sem inventar tamanho quando ambíguo | Objetivo confirmado; implementação automática pendente |
| RF-08 | Verificar presença/estado dos furos previstos, recortes e investigar falhas de corte | Objetivo confirmado; IA e validação pendentes |

**Sobre as imagens anteriores:** o responsável informa que os três vazadores da lingueta **aparecem, mas são minúsculos**. O tamanho exato em milímetros, o grau de abertura e a validação por medição **não foram fornecidos**. Não confundir esse relato com laudo metrológico ou com confirmação de acerto do algoritmo.

## 3. Resultado desejado na interface

1. Selecionar trabalho/lote e carregar referência CAD (ou catálogo controlado).
2. Capturar uma peça e indicar se a foto é utilizável.
3. Mostrar referências CAD candidatas com explicação, `não identificado` ou `ambíguo` quando necessário.
4. Exibir sobreposição e inspeção dos vazadores/recortes CAD, cada um com posição, região da imagem e estado preliminar.
5. Investigar também **regiões fora do CAD** para não perder aberturas extras/deslocadas.
6. Permitir revisão humana e preservar vínculo com revisão CAD, captura e modelo de IA.
7. **Somente após homologação** incorporar decisão de conformidade e tolerâncias aprovadas pela Qualidade.

## 4. Estados recomendados por região

`abertura_compativel_observada`, `suspeita_ausente_ou_incompleta`, `suspeita_deslocada`, `sinal_extra_suspeito`, `recorte_a_revisar`, `inconclusivo`. São **estados de diagnóstico**, não vereditos industriais. A confirmação física é um campo separado, fornecido por revisão autorizada.

## 5. Requisitos não funcionais propostos (a validar)

- IA executada em serviço/worker central com fila, isolamento de falhas e modelo versionado; nada de instalar pesos nos computadores dos operadores.
- Privacidade: fotos, CADs e anotações em armazenamento autorizado, não no repositório público; autenticação e trilha de auditoria antes de uso corporativo.
- Controle da câmera, exposição, iluminação e resolução para distinguir **o menor furo relevante** da trama.
- Metas de latência, concorrência, sensibilidade, alarmes falsos, disponibilidade e critérios de aceite **a negociar com Produção/Qualidade** — ainda não definidos.
- Capturas inconclusivas não geram aprovação automática, assim como a ausência de sinal não prova que o furo esteja ausente.

## 6. Fora do escopo do protótipo atual

Homologação de produção, tolerâncias dimensionais em mm, implantação corporativa, aquisição de câmera, calibração, garantia de precisão e aprovação automática. PostgreSQL e autenticação são previstos para etapa posterior.

## 7. Referências

- [Arquitetura](ARQUITETURA_SISTEMA.md)
- [Protocolo de cabine](CABINE_CAMERA_FIXA_VAZADORES_PROTOCOLO.md)
- [Dados e avaliação](DADOS_TREINAMENTO_VALIDACAO.md)
- [Plano mestre](../PLANO_DESENVOLVIMENTO.md)
