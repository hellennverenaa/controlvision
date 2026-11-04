# ControlVision — arquitetura de IA sob demanda (proposta)

**Data:** 04/11/2026  
**Situação:** proposta técnica para decisão, **não implementada nem aprovada como arquitetura definitiva**.  
**Etapa:** E2.2, experimentação SAM 2.

## Pergunta de produto

O operador precisa instalar uma IA no próprio computador? **Não.** O modelo pode ser executado por um serviço dedicado controlado pela organização ou por um provedor externo, enquanto a interface Vue e a API FastAPI continuam acessíveis pelo navegador.

O laboratório local `~/Documentos/ambiente_dass/sam2-lab/.venv` serve **apenas para investigação**, não representa requisito de instalação nas máquinas dos operadores. A execução de inferência local não foi validada.

## Alternativas

| Alternativa | Pontos positivos | Restrições / riscos |
|---|---|---|
| Local na máquina do operador | Testes offline, nenhum envio de imagem para outra máquina | Replicação de dependências, consumo de RAM/CPU, manutenção |
| Serviço de IA em servidor interno | Centraliza modelos, controle de dados, atualizações independentes | Exige provisionamento, autenticação, recursos computacionais, observabilidade |
| API externa | Sem operar modelo próprio, escalonamento gerenciado | Privacidade de moldes/fotos, contratos, custos, disponibilidade e conformidade |

**Direção recomendada para projeto:** contrato de provedores e **IA opcional**, sem substituir OpenCV; avaliar serviço corporativo interno como opção preferencial para imagens proprietárias. API externa só após aprovação explícita sobre segurança/privacidade, fornecedores, custo e retenção de dados.

## Fluxo sugerido

1. Operador importa CAD e foto pela interface; FastAPI faz validação, proteção dos dados e análise convencional.
2. Orquestrador decide se vale consultar IA (solicitação explícita, falha/inconclusão do baseline, ou experimento habilitado).
3. Adaptador de segmentação chama o provedor configurado (`local_experimental`, `servidor_interno`, ou `api_externa`), com timeout, limites e identificação do modelo.
4. Resposta padronizada preserva `method`, `status`, máscara, avisos, versão e necessidade de revisão humana. Falha ou indisponibilidade da IA **não é sucesso inventado**.
5. OpenCV + geometria CAD seguem independentes para validações geométricas; nenhum resultado de IA autoriza medição em mm, aceitação/rejeição ou liberação de produção.

`backend/app/segmentation_contract.py` e `frontend/src/segmentationComparison.ts` já estabelecem conceitos úteis para preservar um contrato consistente; **um sistema de provedores ainda não foi implementado**.

## Segurança e operação antes de produção

- Não enviar CAD, fotos ou anotações proprietárias a serviços externos sem aprovação.
- Definir autenticação/autorização, processamento assíncrono, limites de tamanho, rate limiting e rastreabilidade.
- Estabelecer política de retenção, criptografia em trânsito/repouso, remoção de artefatos e segregação por cliente/unidade.
- Avaliar custos, latência, filas, disponibilidade, manutenção dos modelos e testes com referência humana.
- Validar qualidade de segmentação com métricas reproduzíveis; SAM 2 não é detector industrial de vazadores nem sistema metrológico.

## E2.2 — evidência adicional da instalação CPU-only

Saída fornecida pelo operador:

```text
Using Python 3.12.16 environment at: sam2-lab/.venv
Installed 13 packages
torch==2.15.0+cpu
torchvision==0.29.2+cpu
```

O teste de importação (`import torch, torchvision`, versões, CUDA e tensor) foi **interrompido pelo operador com Ctrl+C** durante `import torch` e terminou em `KeyboardInterrupt`. Portanto **a instalação dos pacotes foi confirmada, mas a importação/funcionamento não foi verificada**. Isso não demonstra incompatibilidade ou defeito.

Últimos recursos informados: `8,2 GiB` RAM disponível, `1,9 GiB` swap utilizada, `31 GiB` de disco disponíveis. Sem pesos SAM 2 e sem inferência real registrada.

## Decisão pendente e próximo passo

**Suspender novos downloads** até escolher onde a IA será executada e confirmar a política para dados industriais. Não apagar o laboratório criado nem marcar E2.2 concluída. Se houver necessidade de continuar a prova de conceito local, repetir primeiro teste mínimo de importação sem interrupção, com limite operacional de tempo e monitoramento; a alternativa é ensaio em ambiente de servidor próprio. Registrar decisão e resultados no plano mestre.
