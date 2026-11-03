# Procedimento de desenvolvimento, GitHub e documentação

**Aplicação:** ControlVision, branch `feat/prototipo-validacao`.
**Acordado em:** 03/11/2026.
**Situação:** regra de trabalho; não comprova execução de experimento.

## Regras obrigatórias por entrega

1. Antes de modificar arquivos, consultar `PLANO_DESENVOLVIMENTO.md` e a documentação técnica correspondente. Confirmar a branch e o estado do repositório; evitar sobrescrever alterações locais do operador.
2. Implementar mudanças pequenas e rastreáveis. Não incluir fotos, moldes CAD proprietários, credenciais, checkpoints ou ambientes virtuais no repositório público.
3. Adicionar ou atualizar testes apropriados. Executar os testes viáveis e registrar exatamente os resultados, incluindo quaisquer verificações não executadas.
4. Atualizar **na mesma entrega** o `PLANO_DESENVOLVIMENTO.md`: etapa/subetapa, decisões, evidências, riscos, limitações, próximo passo e status verdadeiro. Nunca marcar como concluída uma atividade não realizada.
5. Criar um arquivo **`.md` específico em `docs/` para cada assunto técnico novo** e atualizar os documentos existentes relacionados quando houver mudança. Para resultados de experimentos, registrar configuração, procedimento, evidências e resultados observados, diferenciando fatos de hipóteses.
6. Registrar cada entrega em commit descritivo e enviar para o GitHub na branch de trabalho `feat/prototipo-validacao`. Compartilhar link e SHA do commit e situação da verificação/CI.
7. Manter o PR #1 em rascunho e não mesclar em `main` sem revisão. Em caso de erro no commit/push, informar claramente o bloqueio; não afirmar entrega remota sem confirmação.
8. Quando a etapa depender de execução no computador do operador, fornecer comandos verificáveis, aguardar o resultado observado antes de registrar sucesso, e depois documentar essa evidência no GitHub.

## Estado de continuidade — E2.2

O diagnóstico disponível descreve Ubuntu 26.04.1, Python do sistema 3.14.4, 14 GiB de RAM com 4,2 GiB disponíveis na ocasião, swap de 4 GiB com 2 GiB em uso e `nvidia-smi` indisponível. Isso não prova ausência de GPU. O SAM 2 real ainda não foi executado.

**Pendente de execução pelo operador:** verificar/instalar `uv`, instalar Python 3.12 para o usuário, criar `~/Documentos/ambiente_dass/sam2-lab/.venv` fora do repositório e coletar `python --version`, `which python`, `free -h`, `df -h "$HOME"`. Não instalar torch/SAM 2/checkpoints antes de revisar esses resultados.

**Referências:** `PLANO_DESENVOLVIMENTO.md`, `docs/SAM2_PREPARACAO_E2.md`. A preparação **não está concluída**.
