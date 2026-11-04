# Política de desenvolvimento e documentação — ControlVision

**Revisão:** 04/11/2026 · **Branch de trabalho:** `feat/prototipo-validacao`.

## Entrega obrigatória

1. Antes de desenvolver, ler [Plano mestre](../PLANO_DESENVOLVIMENTO.md), [Requisitos](REQUISITOS_PRODUTO.md) e o documento técnico relevante.
2. Fazer alteração pequena e rastreável; adicionar/atualizar testes cabíveis, registrar falhas e verificações não executadas.
3. Para cada assunto técnico novo, criar arquivo próprio em `docs/`; atualizar os documentos existentes impactados e a situação real do plano **na mesma entrega**.
4. Criar **commit** descritivo e **push** na branch de validação; conferir SHA remoto e CI. Se falhar, declarar bloqueio; não afirmar que enviou.
5. Manter PR #1 em rascunho; não mesclar na `main` sem revisão.
6. Não incluir fotos, CADs proprietários, pesos/checkpoints, datasets, credenciais, tokens ou ambientes virtuais no Git público.
7. Não confundir **proposta, implementação, teste sintético, teste real e homologação**; cada um demanda evidência diferente.

## Organização documental

- README da raiz: visão rápida, execução e links.
- `docs/README.md`: índice.
- `docs/REQUISITOS_PRODUTO.md`: problema, requisitos confirmados e escopo.
- `docs/ARQUITETURA_SISTEMA.md`: componentes atuais e arquitetura futura.
- `PLANO_DESENVOLVIMENTO.md`: estado **atual**, roadmap e próximo marco.
- Documentos técnicos específicos: contratos, experimentos e fontes.
- História de decisões antigas: GitHub commits e documentos de evidência.

**Estado atual não deve ser duplicado aqui**; conferir sempre o plano mestre.
