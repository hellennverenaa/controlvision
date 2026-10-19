# Matriz de validação do ControlVision

## Requisitos já alinhados

- Interface Vue 3 + TypeScript; backend Python + FastAPI.
- Leitura DXF e HPGL/PLT, incluindo arquivos de encaixe com várias peças e numerações.
- Seleção pela lista e pelo clique direto no desenho.
- Classificação provisória dos contornos internos, com revisão humana obrigatória.
- As camadas CAD podem indicar empilhamento da matéria-prima e não determinam vazadores.
- Fotografias e webcam comum são suficientes para experimentos de detecção.
- O banco de produção será PostgreSQL, mas sua integração fica para depois da validação.
- Autenticação e hospedagem corporativas também ficam para uma etapa posterior.
- Tolerâncias serão definidas pelo setor de Qualidade após ensaios metrológicos.

## Testes com arquivos reais feitos fora do repositório

- DXF contendo uma peça dentro de bloco INSERT e geometrias internas.
- DXF contendo um conjunto de peças e textos auxiliares, com candidatos adicionais que precisam de revisão manual.
- Par de arquivos DXF/HPGL de uma mesma distribuição de peças.
- Nenhum dos arquivos proprietários foi incluído no GitHub.

## Próximas validações

1. Revisar nomes, número, lateralidade e contornos dos moldes importados.
2. Testar vazadores circulares e recortes complexos.
3. Confirmar a correspondência das geometrias DXF versus HPGL e as escalas usadas.
4. Corrigir heurísticas que produzem contornos candidatos extras.
5. Calibrar câmera e mesa e medir repetibilidade e incerteza em condições reais.
6. Definir tolerâncias e risco de falsos aceites/falsas rejeições junto com Qualidade.
7. Integrar persistência, controle de revisão e infraestrutura somente após validação.

## Critério de segurança

Esta versão não mede dimensionalmente em milímetros, não aprova/reprova peças e não deve ser usada para liberar produção. O repositório é público: evite subir moldes ou imagens proprietárias.
