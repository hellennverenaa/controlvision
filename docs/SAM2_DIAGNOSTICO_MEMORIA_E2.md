# E2.2 — Diagnóstico de memória antes de instalar SAM 2

**Data da evidência:** 04/11/2026 (relato do operador).  
**Fonte:** saída de comandos locais fornecida na conversa; não houve acesso remoto nem execução local deste diagnóstico pelo assistente.  
**Status:** diagnóstico registrado; nenhuma instalação adicional de IA, inferência ou ajuste de swap foi executado.

## Contexto

O `uv` 0.13.7 e o Python 3.12.16 já foram instalados em ambiente isolado em `~/Documentos/ambiente_dass/sam2-lab/.venv` (fora do ControlVision). O ensaio planejado é SAM 2.1 `tiny`, inicialmente na CPU, sem alterar o backend principal. A E2.2 **ainda não está concluída**.

## Observações em 04/11/2026

```text
free -h
               total       usada       livre    compart.  buff/cache  disponível
Mem.:           14Gi        12Gi       985Mi       1,5Gi       2,5Gi       2,5Gi
Swap:          4,0Gi       3,9Gi        63Mi

swapon --show
NAME      TYPE SIZE USED PRIO
/swap.img file   4G 3,9G   -1

ps -eo pid,comm,%mem,rss --sort=-rss | head -n 16
    PID COMMAND         %MEM   RSS
1049826 Isolated Web Co 31.1 4761624
  70242 firefox          4.5 696224
1191399 Isolated Web Co  4.3 671076
1556859 Isolated Web Co  3.4 525964
1678954 code             3.1 476084
  70819 WebExtensions    2.7 417132
1678643 code             2.2 347336
3347676 Isolated Web Co  1.8 289636
2448007 Isolated Web Co  1.8 286316
  60124 gnome-shell      1.8 277860
2297402 Isolated Web Co  1.6 256284
2517140 Isolated Web Co  1.6 248596
1678345 code             1.5 230296
1682193 code             1.5 229580
2478491 Isolated Web Co  1.5 228996

df -h "$HOME"
/dev/nvme0n1p5  149G  110G  31G  79% /
```

O processo `Isolated Web Co` de maior RSS utiliza 4.761.624 KiB (aproximadamente **4,54 GiB**). O nome é compatível com processo isolado de conteúdo web do Firefox, mas o comando não identifica aba ou causa. RSS pode incluir páginas compartilhadas entre processos e **não deve ser somado diretamente** para estimar memória exclusiva. Os valores são instantâneos e podem variar.

Há **2,5 GiB de RAM disponível** e **3,9 GiB de 4 GiB de swap ocupados**; é prudente evitar cargas grandes antes de reavaliar o ambiente. Swap ocupada não comprova, isoladamente, troca ativa de páginas ou falha iminente. O espaço em disco de 31 GiB não elimina riscos de memória.

## Próximos passos seguros (somente operador)

1. Salvar trabalhos e fechar abas dispensáveis; opcionalmente reiniciar o Firefox depois de preservar sessões/dados, sem terminar processos à força.
2. Reexecutar `free -h` e `ps -eo pid,comm,%mem,rss --sort=-rss | head -n 16`.
3. Se disponível, observar atividade de swap com `vmstat 1 5` (colunas `si` e `so`); as primeiras linhas podem apresentar médias desde boot, portanto considerar as amostras subsequentes.
4. Compartilhar os números para decisão sobre instalar dependências CPU-only e testar o SAM 2 com limite de recursos e fotografia não proprietária.

**Não executar automaticamente:** `kill`, `swapoff`, limpeza de caches, ajuste de swap, instalação de torch/SAM 2 ou download de checkpoints. O próximo passo é reavaliar memória depois de reduzir o consumo do navegador.

## Critério de continuidade

Não há neste momento evidência de memória suficiente para carregar com segurança o modelo nesta sessão. Após novo diagnóstico, escolher um ensaio pequeno e supervisionado ou adiar a execução. **E2.2 permanece aberta**; implementação do laboratório Python já concluída, instalação e inferência de IA ainda pendentes.
