# IA sob demanda — decisão arquitetural proposta

**Revisão:** 04/11/2026. **Estado:** direção confirmada de acesso via web multi-posto; detalhes de servidor, fila e modelos **pendentes de implementação**.

## Por que IA centralizada?

O ControlVision será acessado por vários computadores da produção. O objetivo é que **nenhum operador precise instalar modelos ou PyTorch**: o navegador envia capturas à API e um serviço central processa tarefas pesadas, com proteção dos dados proprietários.

A cabine existe, mas a câmera fixa ainda não foi escolhida nem instalada. O laboratório Python 3.12 com PyTorch CPU no computador de desenvolvimento é **somente experimental**.

## Estratégia proposta

```text
Postos web -> API FastAPI / autenticação futura
          -> fila / armazenamento privado
          -> serviço IA isolado
               máscara da peça
               ranking CAD (modelo/numeração/desconhecido)
               inspeção por patches dos vazadores/recortes + busca global
          -> resultados explicáveis + revisão humana
```

OpenCV e operações geométricas são mantidos como referência. IA é usada quando agrega evidência mensurável. **SAM 2 é candidato para máscara externa/anotação, não detector de microvazadores validado.** Modelos para trama/vazadores ainda precisam de rótulos físicos. Falha de IA retorna `indisponivel` / `inconclusivo`, não aprovação.

## Implantação a decidir

- Serviço em servidor controlado pela empresa ou infraestrutura contratada com exigências de privacidade.
- CPU/GPU, filas, autenticação, PostgreSQL, controle de versões, retenção, observabilidade, limites e capacidade simultânea **pendentes**.
- API externa somente com aprovação explícita de segurança, políticas e contratos para fotos/CAD privados.
- Separar tarefas e métricas: segmentação da peça, reconhecimento CAD e inspeção física de microfuros.

## Situação comprovada

Código atual: módulo SAM 2 opcional, contrato de máscara v1, sem execução do modelo real. Laboratório isolado: torch 2.15.0+cpu e torchvision 0.29.2+cpu instalados, mas o teste de importação foi interrompido (`KeyboardInterrupt`). Não há treino, inferência real nem serviço central implementado.

Detalhamento: [Arquitetura geral](ARQUITETURA_SISTEMA.md), [Pesquisa aplicada](PESQUISA_IA_INSPECAO_TRAMAS_CAD_2026-11-04.md) e [Plano](../PLANO_DESENVOLVIMENTO.md).
