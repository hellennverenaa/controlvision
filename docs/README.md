# Documentação do ControlVision

**Fonte de verdade:** esta página orienta a leitura. O `README.md` da raiz apresenta o produto; `PLANO_DESENVOLVIMENTO.md` registra o **estado atual e próximos passos**. Arquivos técnicos registram contratos, experimentos e evidências.

## Essencial para entrar no projeto

1. [Visão do produto e requisitos](REQUISITOS_PRODUTO.md) — o que é a aplicação, objetivos confirmados, escopo e limites.
2. [Arquitetura do sistema](ARQUITETURA_SISTEMA.md) — módulos que existem hoje e arquitetura web/IA prevista.
3. [Plano mestre](../PLANO_DESENVOLVIMENTO.md) — andamento, critérios e próximos marcos.
4. [Dados, treino e validação](DADOS_TREINAMENTO_VALIDACAO.md) — rotulagem, métricas e primeiro experimento P0.
5. [Regras de desenvolvimento/GitHub](FLUXO_TRABALHO_GITHUB.md) — documentação, testes, commit/push e segurança.

## Cabine e caso real

- [Cabine fixa e protocolo de furos passantes](CABINE_CAMERA_FIXA_VAZADORES_PROTOCOLO.md)
- [Evidências anteriores da lingueta](EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md)
- [Pesquisa de modelos e projetos públicos](PESQUISA_IA_INSPECAO_TRAMAS_CAD_2026-11-04.md)

## Referências técnicas ainda válidas

- [Contrato de máscaras v1](SEGMENTACAO_CONTRATO.md)
- [Métricas de segmentação](SEGMENTACAO_METRICAS.md)
- [SAM 2: módulo e execução opcional](SAM2_EXECUCAO_EXPERIMENTAL.md)
- [SAM 2: preparação E2, incluindo histórico dos comandos](SAM2_PREPARACAO_E2.md)
- [Diagnósticos de memória do laboratório](SAM2_DIAGNOSTICO_MEMORIA_E2.md) — histórico, não instrução de status atual.
- [Arquitetura de IA sob demanda — discussão e decisões preliminares](ARQUITETURA_IA_SOB_DEMANDA.md)

## Organização e limpeza editorial de 04/11/2026

- O `README.md` da raiz foi simplificado: detalhes antigos de experimentos foram retirados **da página inicial**, mas podem ser consultados no histórico do GitHub; evidências relevantes foram consolidadas em `EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md` e demais documentos experimentais.
- O plano mestre foi reestruturado para deixar **estado atual e pendências** à vista; os registros pormenorizados antigos continuam acessíveis em commits anteriores e nos documentos experimentais.
- `docs/VALIDACAO.md` foi removido por repetir requisitos e pendências já cobertos por `REQUISITOS_PRODUTO.md` e `DADOS_TREINAMENTO_VALIDACAO.md`; conteúdo histórico preservado no Git.
- **Nenhum código, teste ou fotografia de fábrica foi alterado/versionado nesta revisão.** Nenhuma evidência de treino ou homologação foi criada.

### Convenções

Documentos novos em `docs/`. Registrar como **confirmado**, **proposto**, **implementado**, **testado** ou **pendente**, sem confundir as categorias. Dados industriais permanecem privados. Cada entrega inclui atualização do plano, testes cabíveis e commit/push na branch de validação; PR #1 permanece em rascunho.
