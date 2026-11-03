# SAM 2.1 — preparação do primeiro ensaio real (E2.1)

**Revisão da documentação oficial:** 03/11/2026.
**Status da E2.1:** fontes, dependências, pareamento dos checkpoints e
pré-requisitos **verificados no código e por testes sintéticos**.
**Não há modelo real instalado/carregado/executado neste repositório ou no CI.**
**Próxima etapa: E2.2 (instalação e primeira execução em ambiente isolado).**

## Decisão de arquitetura

Experimentar **Meta SAM 2.1, variante `tiny`, com prompt de caixa derivado
do contorno OpenCV**. Este é um teste de *segmentação assistida*, **não**
uma prova de reconhecimento independente. Não treinar U-Net ainda.

Continuamos com o detector OpenCV no caminho normal do ControlVision.
O módulo `backend/app/sam2_optional.py` permanece **desativado por padrão**,
só atuando na rota experimental após habilitação local. A aplicação não
faz download automático de código nem de modelos.

## Fontes oficiais consultadas

- Código, descrição, checkpoints e licença:  
  https://github.com/facebookresearch/sam2
- Requisitos e resolução de problemas:  
  https://github.com/facebookresearch/sam2/blob/main/INSTALL.md
- Texto da licença:  
  https://github.com/facebookresearch/sam2/blob/main/LICENSE
- Pacotes requeridos:  
  https://github.com/facebookresearch/sam2/blob/main/setup.py
- Lista exata de arquivos oficiais:  
  https://github.com/facebookresearch/sam2/blob/main/checkpoints/download_ckpts.sh

### Licenciamento

O repositório oficial declara que **código, pesos e componentes de
treinamento do SAM 2 são distribuídos sob Apache 2.0**. Essa licença é
permissiva e admite uso comercial **com as condições aplicáveis**,
incluindo manutenção de avisos de licença e atribuição quando distribuídos.
As fontes também mencionam licença separada para alguns recursos da demo
(fontes). Antes de distribuir software ou pesos fora do laboratório,
revisar os avisos de terceiros e a política jurídica da empresa.

**A licença do dataset interno de fotos de calçados não decorre da licença
do SAM 2.** Fotografias da fábrica e anotações permanecem privadas.

### Ambiente recomendado

| Verificação | Requisito ou decisão |
|---|---|
| Sistema operacional | **Linux** recomendado pelo projeto; Windows preferencialmente em WSL 2 |
| Python | **>= 3.10** |
| PyTorch | **>= 2.5.1** |
| TorchVision | Oficialmente **>= 0.20.1** e compatível com a versão de PyTorch instalada |
| CUDA | Opcional no primeiro ensaio, mas GPU NVIDIA é preferível para velocidade; driver/toolkit/VRAM precisam ser validados localmente |
| Extensão CUDA do SAM 2 | Pode não compilar; `SAM2_BUILD_CUDA=0` desativa compilação (também elimina parte do pós-processamento) |
| Hardware, tempo, memória e custo | **Não medidos**. Primeira carga, tempo por foto, VRAM e custo operacional serão registrados em E2.2 |
| Integração ControlVision | A execução SAM 2 consome recursos do mesmo servidor de laboratório se ativada; não há isolamento de processo |
| Imagens de produção | Não enviar a repositórios, datasets públicos ou serviços externos |

**Não é possível garantir execução CPU em todas as configurações**;
o projeto foi desenvolvido com foco em GPU e alguns kernels/atenção
podem não funcionar em instalações CPU-only. Se o primeiro ensaio falhar,
registrar os requisitos concretos em vez de afirmar que o teste funcionou.

## Pareamento oficial — SAM 2.1

| `CONTROLVISION_SAM2_VARIANT` | Configuração Hydra | Checkpoint esperado |
|---|---|---|
| `tiny` | `configs/sam2.1/sam2.1_hiera_t.yaml` | `sam2.1_hiera_tiny.pt` |
| `small` | `configs/sam2.1/sam2.1_hiera_s.yaml` | `sam2.1_hiera_small.pt` |
| `base_plus` | `configs/sam2.1/sam2.1_hiera_b+.yaml` | `sam2.1_hiera_base_plus.pt` |
| `large` | `configs/sam2.1/sam2.1_hiera_l.yaml` | `sam2.1_hiera_large.pt` |

**Cuidado:** o arquivo existir e ter o nome correto **não comprova** que
seja um checkpoint autêntico ou íntegro. Nunca carregar arquivos `.pt`
de origem desconhecida. Obter da fonte oficial e registrar versão,
local, tamanho e hash SHA-256 **fora do GitHub público** para auditoria.

Fonte oficial dos checkpoints:  
https://github.com/facebookresearch/sam2/blob/main/checkpoints/download_ckpts.sh

URL oficial específica do modelo `tiny` conforme script da Meta:  
https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt

**Não foi feito download** nesta etapa; o URL é referência para a E2.2.

## Diagnóstico local e seguro

Na pasta do backend, usando o interpretador Python do ambiente de
laboratório pretendido (não exige instalar o SAM 2 para fazer o diagnóstico):

```bash
cd ~/Documentos/ambiente_dass/controlvision/backend
python3 -m app.sam2_preflight
```

O comando imprime JSON com `status`, `issues`, `packages` e
`warnings`, sem baixar pesos e sem abrir o checkpoint. Não informa
caminhos absolutos privados.

**Diagnóstico observado no Linux do operador em 03/11/2026:** Python `3.14`,
`status=desativado`, bibliotecas `torch`, `torchvision` e `sam2` ausentes
e nenhum checkpoint configurado. Isso **não é falha do diagnóstico**: mostra
que o laboratório ainda não foi instalado. A seleção `device=cpu` é
configuração padrão, **não** comprovação de inexistência de placa NVIDIA.

**Compatibilidade Python:** distribuições recentes de PyTorch publicam
suporte a Python 3.14 (consulte https://pytorch.org/get-started/locally/).
O SAM 2 declara mínimo Python 3.10, mas a combinação exata de SAM 2,
torchvision, extensões e drivers **não foi testada neste computador**.
Preferir, se já disponível, Python 3.12 em uma `venv` dedicada para um
ensaio controlado; não alterar o Python 3.14 do sistema. Se não houver Python
3.12, decidir a opção de instalação após verificar distribuição Linux,
hardware, drivers e versões de PyTorch disponíveis.

**Coleta segura para o próximo passo, sem instalar nada:**

```bash
. /etc/os-release; echo "$PRETTY_NAME"
for p in python3.12 python3.11; do command -v "$p" >/dev/null && "$p" --version; done
if command -v nvidia-smi >/dev/null; then nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; else echo "nvidia-smi não disponível"; fi
free -h
```

Caso `nvidia-smi` não exista, isso significa apenas que o utilitário/driver
não está disponível, e **não** prova que o computador não possui GPU. Sem `CONTROLVISION_SAM2_ENABLED=1`, o status
será `desativado` mesmo que todas as bibliotecas existam.

Para analisar uma configuração de **futuro teste** (sem executar IA):

```bash
CONTROLVISION_SAM2_ENABLED=1 \
CONTROLVISION_SAM2_VARIANT=tiny \
CONTROLVISION_SAM2_DEVICE=cpu \
CONTROLVISION_SAM2_CHECKPOINT=/caminho/privado/sam2.1_hiera_tiny.pt \
python3 -m app.sam2_preflight
```

- `pendente`: falta pré-requisito, configuração ou checkpoint local.
- `desativado`: segurança padrão, IA não habilitada.
- `prerequisitos_presentes`: **somente verificação estática**;
  não comprova integridade dos pesos nem que a inferência vai funcionar.
- `gpu_verified=false` sempre nesta etapa, pois não há importação de
  PyTorch e a GPU não é testada.
- `performance_measured=false` e `model_executed=false` sempre.
- A comparação de versões não substitui a matriz real de compatibilidade
  PyTorch/TorchVision/CUDA; o diagnóstico adverte sobre isso.

Os testes estão em `backend/tests/test_sam2_preflight.py` e
`backend/tests/test_sam2_optional.py`. O executor recusa explicitamente
checkpoint com nome de variante incompatível, **antes de tentar inferir**.

## Diagnóstico da máquina de laboratório — 03/11/2026

Informações fornecidas pelo operador, sem acesso remoto ao computador:

| Item | Estado observado |
|---|---|
| Sistema | Ubuntu **26.04.1 LTS** (Linux) |
| Python do sistema | **3.14.4**; `python3.11`, `python3.12` e `python3.13` não encontrados no `PATH` |
| RAM total | **14 GiB** |
| RAM disponível no momento | **4,2 GiB** (a medida varia com aplicativos abertos) |
| Swap | **4,0 GiB**, dos quais **2,0 GiB em uso** |
| NVIDIA | `nvidia-smi` **indisponível**; não demonstra ausência de qualquer GPU |
| SAM 2 | desativado; não há `torch`, `torchvision`, `sam2` ou checkpoint neste Python |
| Memória/velocidade do SAM 2 real | **não medidas** |

**Decisão para E2.2:** começar preparando um **Python 3.12 em ambiente isolado**,
sem alterar/remover o Python 3.14 do Ubuntu. Priorizar **CPU** apenas como
ensaio de viabilidade (não prometer desempenho), já que nenhuma GPU NVIDIA foi
confirmada. Antes de executar uma inferência pesada, fechar aplicações que
estejam consumindo memória e reavaliar `free -h`. Os **4,2 GiB disponíveis**
e o uso de swap recomendam cautela; a capacidade suficiente para processar
uma fotografia real ainda não foi comprovada.

### Preparação segura do laboratório (sem instalar SAM 2 por enquanto)

O projeto [uv](https://docs.astral.sh/uv/) permite gerenciar Python 3.12
para o usuário sem trocar o interpretador do sistema. O laboratório ficará
**fora da pasta do repositório ControlVision**.

Se `uv --version` funcionar, pule a instalação de `uv`. Caso contrário,
use o instalador oficial da Astral apenas após conferir sua origem:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

Depois execute:

```bash
cd ~/Documentos/ambiente_dass
uv python install 3.12
mkdir -p sam2-lab
uv venv --python 3.12 sam2-lab/.venv
source sam2-lab/.venv/bin/activate
python --version
which python
free -h
```

**O esperado nesta fase:** `Python 3.12.x` e um caminho terminado em
`sam2-lab/.venv/bin/python`; nenhuma biblioteca de IA foi instalada ainda.
Não executar `sudo apt install python3.12` como primeira opção no Ubuntu
26.04, pois isso envolveria alterar pacotes de sistema. Não usar
`pip install` fora do ambiente virtual. Não carregar o checkpoint nesta etapa.

A instalação futura de PyTorch/torchvision será **CPU-only** e deve seguir
o seletor oficial de versões compatíveis em
https://pytorch.org/get-started/locally/ ; a instalação SAM 2 deve seguir
https://github.com/facebookresearch/sam2/blob/main/INSTALL.md com
`SAM2_BUILD_CUDA=0` quando apropriado. Não há necessidade de escolher
ou instalar CUDA sem GPU confirmada. Confirmar **espaço em disco disponível**
com `df -h` antes de baixar pesos e bibliotecas.

**Status do plano:** E2.2 **em preparação; não concluída**. A escolha de
Python 3.12 é conservadora para reduzir possíveis incompatibilidades de
bibliotecas de IA; não indica que o Python 3.14 esteja incorreto.

## Roteiro para a próxima etapa (E2.2)

1. Criar um **ambiente Python separado** do backend habitual, com versões
   de Python, torch e torchvision compatíveis com a máquina de laboratório.
2. Instalar código SAM 2 **da fonte oficial**, conferindo licença e
   versão/revisão; em Linux o repositório recomenda `pip install -e .`.
3. Baixar **somente o checkpoint oficial `tiny`** em diretório privado,
   registrar hash/tamanho e executar o preflight.
4. Medir tempo de carregamento, tempo por fotografia e memória/VRAM em
   computador identificado. Não comparar custos sem hardware conhecido.
5. Executar em foto real apenas depois de configurar ambiente, mantendo
   o OpenCV normal como fallback da aplicação (sem falsificar resultado de IA).
6. Anotar sucesso, falha e limitações; registrar resultados no
   `PLANO_DESENVOLVIMENTO.md`. IoU/Dice só com máscara humana revisada.

**E2.1 não substitui E2.2**: preparação verificada por documentação e
testes sintéticos não é evidência de segmentação com SAM 2 real.


## Ocorrência E2.2 — tentativa de instalar uv com Snap (03/11/2026)

**Relato do operador (ainda sem instalação bem-sucedida):** `uv --version` retornou comando não encontrado. Uma tentativa de `sudo snap install astral-uv` apresentou inicialmente erro de autenticação de `sudo` e, nas tentativas seguintes, a mensagem de que o pacote Snap exige `classic confinement` (`--classic`). **Não há confirmação de instalação do uv via Snap.**

**Decisão:** não ampliar privilégios do pacote Snap apenas para avançar nesta etapa; preferir o instalador standalone oficial da Astral no escopo do usuário, como já previsto neste guia. Conferir o script antes de executá-lo caso a política local exija revisão:

```bash
curl -LsSf https://astral.sh/uv/install.sh | less
# Após conferência do instalador oficial:
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

Fonte: https://docs.astral.sh/uv/getting-started/installation/ . O instalador baixa código externo; usar somente após confiar na origem/revisar o conteúdo. Caso `curl` falhe, interromper e registrar o erro, sem recorrer automaticamente a `sudo` ou `--classic`.

**Critério seguinte, ainda não atendido:** confirmar versão de `uv` no computador; só então instalar Python 3.12 e criar `sam2-lab/.venv`. **E2.2 continua pendente.**


### Confirmação posterior — uv disponível (03/11/2026)

O operador executou `curl -LsSf https://astral.sh/uv/install.sh | sh`, ajustou o `PATH` para `$HOME/.local/bin` e obteve:

```text
installing to /home/hellen/.local/bin
  uv
  uvx
everything's installed!
uv 0.13.7 (x86_64-unknown-linux-gnu)
```

**Verificado por saída de terminal fornecida:** `uv` versão 0.13.7 instalada para o usuário. A mensagem `unrecognized subcommand '0.x.x'` resultou de executar literalmente um exemplo de versão, **não** é falha da instalação. Nenhum comando de Python 3.12 ou criação de `sam2-lab/.venv` foi confirmado ainda.

**Próxima verificação (somente ambiente isolado, sem instalar IA):**

```bash
cd ~/Documentos/ambiente_dass
uv python install 3.12
mkdir -p sam2-lab
uv venv --python 3.12 sam2-lab/.venv
source sam2-lab/.venv/bin/activate
python --version
which python
free -h
df -h "$HOME"
```

A etapa **E2.2 permanece em andamento** até a execução real controlada do modelo e avaliação correspondente.


### E2.2 — Python 3.12 isolado confirmado; RAM/swap precisam de reavaliação (03/11/2026)

**Evidência fornecida pelo operador (não executada remotamente por este assistente):**

```text
uv python install 3.12
Installed Python 3.12.16
uv venv --python 3.12 sam2-lab/.venv
Using CPython 3.12.16
Creating virtual environment at: sam2-lab/.venv
python --version
Python 3.12.16
which python
/home/hellen/Documentos/ambiente_dass/sam2-lab/.venv/bin/python
free -h
Mem.: 14Gi total, 10Gi usada, 1,7Gi livre, 4,5Gi disponível
Swap: 4,0Gi total, 4,0Gi usada, 17Mi livre
df -h "$HOME"
/dev/nvme0n1p5 149G total, 111G usado, 31G disponível, 79% uso
```

**Conclusões verificáveis:** ambiente virtual `sam2-lab/.venv` criado fora do repositório, com Python 3.12.16; `uv` 0.13.7 já confirmado. Os 31 GiB disponíveis de armazenamento precisam ser preservados para arquivos do usuário e futuras dependências; não representam reserva exclusiva de IA. Swap está praticamente todo ocupado, o que **não prova por si só falta de RAM no momento**, mas é um sinal de pressão anterior e possível degradação de desempenho. Medidas são instantâneas e podem mudar.

**Próximo diagnóstico, apenas leitura (sem sudo):**

```bash
free -h
swapon --show
ps -eo pid,comm,%mem,rss --sort=-rss | head -n 16
df -h "$HOME"
```

`rss` é memória residente em KiB, e `%mem` é porcentagem aproximada da RAM física; somas de RSS podem contar páginas compartilhadas mais de uma vez. Revisar processos de maior consumo **sem encerrá-los automaticamente**. Não executar `swapoff`, não instalar bibliotecas pesadas nem baixar checkpoints antes de revisar esse diagnóstico. Não é necessário compartilhar linha de comando completa, variáveis, nomes de arquivos privados ou segredos.

**Estado:** preparação de Python isolado **concluída**; instalação PyTorch/torchvision, SAM 2.1 tiny, pesos e inferência **não realizadas**. E2.2 continua aberta.
