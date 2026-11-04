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


## Segunda coleta — melhora parcial (04/11/2026)

**Evidência recebida do operador:**

```text
free -h
Mem.: 14Gi total, 11Gi usada, 1,8Gi livre, 3,2Gi disponível
Swap: 4,0Gi total, 2,6Gi usada, 1,4Gi livre

ps -eo pid,comm,%mem,rss --sort=-rss | head -n 16
1049826 Isolated Web Co 31.1 4751372
70242 firefox 5.2 806616
1556859 Isolated Web Co 5.1 786792
1191399 Isolated Web Co 4.7 723084
3347676 Isolated Web Co 3.9 598392

vmstat 1 5
[amostra inicial] si=39 so=96
[amostra 2] si=732 so=0
[amostra 3] si=20 so=0
[amostras 4–5] si=0 so=0
```

**Interpretação:** RAM disponível aumentou de 2,5 para **3,2 GiB** (+0,7 GiB), swap ocupada caiu de 3,9 para **2,6 GiB** (−1,3 GiB). Houve alguma leitura de swap durante a coleta (`si` de 732 e 20 KiB/s em amostras intermediárias), sem `so` após a amostra inicial; amostras finais não indicaram trocas. Isso **não caracteriza uso intenso e contínuo de swap** nesse intervalo curto, nem comprova estabilidade sob inferência. O maior processo web permanece com aproximadamente **4,53 GiB de RSS** (4.751.372 KiB), quase inalterado. Nenhuma aba exata foi identificada.

**Decisão:** não iniciar inferência ou instalar dependências pesadas nesta sessão com apenas 3,2 GiB disponíveis. Solicitar ao operador salvar a sessão e **encerrar normalmente** o Firefox quando for conveniente, sem `kill`/`swapoff`, e então colher `free -h` e `ps -eo pid,comm,%mem,rss --sort=-rss | head -n 10`. Como alternativa, usar gerenciador de tarefas do Firefox (`about:processes`) para identificar abas/processos de alto consumo antes de fechá-las. A eventual recuperação da memória será medida, não presumida. Só depois decidir pela instalação experimental CPU-only.

**Estado:** coleta de memória repetida; melhoria parcial confirmada, mas pré-requisitos de execução real do SAM 2.1 tiny e E2.2 seguem **pendentes**. Nenhuma alteração em código, sistema, memória ou modelos foi realizada pelo assistente.


## Terceira coleta — memória liberada (04/11/2026)

**Saída fornecida pelo operador:**

```text
free -h
Mem.: 14Gi total, 5,4Gi usada, 7,5Gi livre, 9,1Gi disponível
Swap: 4,0Gi total, 1,9Gi usada, 2,1Gi livre

ps -eo pid,comm,%mem,rss --sort=-rss | head -n 10
1191399 Isolated Web Co 5.4 829680
70242 firefox 5.2 796544
70819 WebExtensions 3.0 458220
1678954 code 2.3 354004
1678643 code 2.0 319720
60124 gnome-shell 1.5 239400
1678345 code 1.1 182556
71217 Privileged Cont 1.0 164664
1678891 code 1.0 162120
```

**Comparação:** RAM disponível aumentou de 3,2 para **9,1 GiB** (+5,9 GiB); swap utilizada caiu de 2,6 para **1,9 GiB** (−0,7 GiB). O processo de ~4,5 GiB não aparece mais no top 10; o maior processo apresentado agora possui ~810 MiB RSS. Isso é compatível com redução de uso do navegador, mas não prova quais abas foram fechadas nem que swap será estável sob carga. Não houve coleta adicional de `vmstat` nesta rodada; o armazenamento disponível observado anteriormente foi 31 GiB, não medido novamente.

**Decisão de continuidade:** recursos atuais são mais favoráveis para **instalar e testar a importação de bibliotecas CPU-only no `sam2-lab/.venv`**, mas não garantem execução de inferência SAM 2. Instalar primeiro apenas `torch` + `torchvision` da distribuição CPU oficial, conferir versões e um tensor simples; instalar SAM 2 e checkpoint apenas depois dos resultados, de forma incremental. Antes de iniciar inferência real, obter nova medida de memória. Nenhuma instalação de IA foi observada ou executada nesta rodada.

A instrução controlada de instalação está em `docs/SAM2_PREPARACAO_E2.md`. **E2.2 continua aberta.**
