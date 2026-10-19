# Matriz de validação do ControlVision

## Definições confirmadas com a fábrica

- Aplicação web com Vue 3 + TypeScript; Python + FastAPI.
- DXF e HPGL/PLT; encaixes com muitas peças e numerações.
- Seleção de molde tanto pela lista quanto por clique no desenho CAD.
- Camadas da matéria-prima não são identificação de contorno/vazador.
- Vazadores podem ser círculos e recortes internos, sempre com revisão.
- Webcam ou fotografias existentes inicialmente.
- PostgreSQL obrigatório na fase de produção, integração não prioritária agora.
- Servidor Linux, PM2, API Gateway e dass_auth_service: fase posterior.
- Tolerâncias por peça e por região serão discutidas com a Qualidade.
- Peças de costura programada exigem medição muito rigorosa; «zero mm» não é critério metrológico validado.

## O que foi verificado localmente antes desta branch

- Testes unitários sintéticos: DXF com contorno e círculo interno, polilinhas abertas conectadas, HPGL fechado, extensão inválida.
- Arquivo HELLEN.dxf: 1 peça candidata com 6 geometrias internas.
- TEST_TRS-FOR-TRA.dxf: 27 candidatos.
- TEST_TRS-FOR-TRA.PLX.hpgl: 27 candidatos (moldura de plotagem removida por heurística).
- SB CHRON CNVS.dxf: candidatos adicionais indevidos; NÃO considerar identificação validada sem revisão manual.

## O que precisamos validar na aplicação publicada

1. Importação correta de arquivos reais exportados por diferentes máquinas/sistemas.
2. Não perder vazadores, arcos e recortes não circulares.
3. Listagem e seleção visual: clique no desenho seleciona o mesmo item da lista.
4. Identificação confiável do modelo, tamanho, peça e lado; não inferir dados ausentes.
5. Comparação CAD-imagem em mm: ainda não implementada.
6. Calibração de lente e plano, controle de espessura e repetibilidade.
7. Análise de risco de falsos aceites/falsas rejeições com Qualidade.
8. Configuração de tolerâncias após ensaios.
9. Só então integrar banco PostgreSQL, autenticação e infraestrutura corporativa.

## Política de segurança

- O repositório é público: arquivos CAD de produção são potencialmente confidenciais.
- Não inserir fotografias reais nem moldes proprietários no GitHub sem autorização.
- O serviço foi concebido apenas para uso local na etapa de validação.

## Critério de aprovação desta branch

Esta branch pode ser revisada e testada sem risco de ser confundida com uma solução metrológica homologada. Nunca liberar produção com base no protótipo.
