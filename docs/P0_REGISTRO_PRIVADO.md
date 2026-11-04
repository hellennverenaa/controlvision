# P0 — registro privado da peça, CAD e vazadores

**Entrega de 04/11/2026:** esquema simples `p0.1` e validador Python offline. **Não há dataset real nem verificação de furos realizada.**

## Por que este registro?

O CAD determina quais furos passantes devem existir. O operador inspeciona a peça física e registra separadamente se cada região foi **realmente verificada**. A trama natural não pode ser marcada automaticamente como vazador. Um verificador de metadados não analisa imagens, não confirma abertura e não produz aprovação industrial.

## Organização privada sugerida (FORA do repositório Git)

```text
~/Documentos/ambiente_dass/controlvision-dados-privados/
  ensaio-001/
    manifesto.json
    cad/peca.dxf
    fotos/frontal.jpg
    fotos/contraluz.jpg    # opcional, caso exista teste
```

**Nunca** adicionar a pasta privada ao GitHub ou colocar fotos/DXF na pasta versionada. O exemplo `docs/exemplos/p0_manifesto_sintetico.json` contém somente nomes fictícios e **não descreve peça real**.

## Criar um registro

1. Escolher uma peça física real e a revisão correta de seu CAD, em armazenamento privado autorizado.
2. Guardar foto **original sem overlay** e, se viável, uma segunda captura com contraluz.
3. Copiar o exemplo sintético **para a pasta privada** e preencher `peca_fisica_id`, `material`, `cad_revisao`, `revisor`, `cad_arquivo`, `fotografias` e `geometrias`.
4. Para cada `cad_feature_id`, preencher `tipo` (`vazador` ou `recorte`), `estado_fisico` (`aberto`, `ausente_ou_incompleto`, `deslocado` ou `incerto`) e `verificado_fisicamente`. **Sem revisão física, manter `incerto` e `false`**, mesmo que a imagem pareça mostrar um furo.
5. Verificar estrutura sem copiar/abrir as imagens no GitHub:

```bash
cd ~/Documentos/ambiente_dass/controlvision/backend
.venv/bin/python -m app.p0_manifest ~/Documentos/ambiente_dass/controlvision-dados-privados/ensaio-001/manifesto.json --require-files
```

O argumento `--require-files` verifica existência dos arquivos relativos (a partir da pasta do manifesto); não lê pixels, não valida DXF nem determina o diâmetro do furo. Sem a opção, valida somente a estrutura JSON, útil para criar o registro antes das fotos. Use o Python do backend, não é necessário instalar SAM 2.

## Critérios do P0 (continuam pendentes)

- [ ] Peça física e DXF correto separados e autorizados.
- [ ] Vazadores CAD identificados e revisão física registrada.
- [ ] Imagens originais capturadas e iluminação anotada.
- [ ] Visibilidade do menor vazador verificada, sem inventar mm.
- [ ] Referência de máscara humana (externa) criada para comparação OpenCV.
- [ ] Resultados reais armazenados e avaliados **privadamente**.

**Privacidade:** o validador roda offline. O manifesto pode conter identificadores proprietários; não anexá-lo a issues, logs públicos ou repositórios.

## Diagnóstico de ambiente de testes — 04/11/2026

O operador executou `backend/.venv/bin/python -m pytest -q tests/test_p0_manifest.py` e recebeu `No module named pytest`. **Isso só confirma que o pytest não está instalado nesse interpretador; não é resultado dos sete testes do P0.** O `pytest` é ferramenta de desenvolvimento, não dependência necessária para a API em produção. Instalar explicitamente no ambiente virtual do **backend**, não no laboratório `sam2-lab/.venv`:

```bash
cd ~/Documentos/ambiente_dass/controlvision/backend
.venv/bin/python -m pip install pytest
.venv/bin/python -m pytest --version
.venv/bin/python -m pytest -q tests/test_p0_manifest.py
```

Se o comando de instalação informar `No module named pip`, interromper e diagnosticar o ambiente antes de instalar pacotes de outra forma. **Aguardando saída da instalação e dos testes para registrar aprovação ou falha real.** Nenhuma foto, CAD ou máscara privada precisa ser fornecida para esses testes sintéticos.


## Execução local confirmada — 04/11/2026

O operador instalou `pytest==9.2.0` no ambiente `controlvision/backend/.venv` e forneceu a saída da execução:

```text
.venv/bin/python -m pytest --version
pytest 9.2.0
.venv/bin/python -m pytest -q tests/test_p0_manifest.py
....... [100%]
7 passed in 0.01s
```

**Conclusão:** os sete testes sintéticos do validador de manifesto P0 foram aprovados no computador do operador. Esta evidência não inclui suíte completa, análise de fotografia real, verificação física de furos, integração com IA ou homologação industrial. Os arquivos privados do ensaio-001 ainda precisam ser preparados e revisados.


## Suíte completa do backend — execução local em 04/11/2026

O operador executou no ambiente virtual do backend:

```bash
cd ~/Documentos/ambiente_dass/controlvision/backend
.venv/bin/python -m pytest -q
```

Resultado fornecido:

```text
........................................................ [ 40%]
........................................................ [ 80%]
............................                             [100%]
140 passed in 2.93s
```

**Conclusão:** regressão automatizada completa do backend passou nesta execução local. Os **7 testes de estrutura do manifesto P0** integram essa suíte. Isso **não** demonstra reconhecimento de vazadores em fotos reais, revisão física, treinamento de IA, calibração ou homologação. Também não substitui testes de frontend e E2E. Próximo passo permanece a preparação de um ensaio privado com uma lingueta física, seu DXF correto e fotos originais.


## Verificação inicial do manifesto copiado — 04/11/2026

Operador confirmou criação de `controlvision-dados-privados/ensaio-001/{cad,fotos}` e cópia do exemplo `p0_manifesto_sintetico.json` para `manifesto.json`. A execução com `--require-files` retornou:

```text
ERRO: cad_arquivo: arquivo não encontrado
ERRO: fotografias[0].arquivo: arquivo não encontrado
```

**Diagnóstico:** resultado esperado para manifesto sintético que aponta para `cad/arquivo_exemplo.dxf` e `fotos/frontal_exemplo.jpg`, ainda não existentes. **Não representa falha do validador nem confirmação de ensaio real.** Próxima ação: localizar o DXF correto e a foto original sem overlay em armazenamento autorizado, copiar para a pasta privada e ajustar os caminhos relativos no manifesto. Não criar arquivos fictícios para fazer o teste passar. Manter estados físicos `incerto`/`false` até revisão individual, e não publicar caminhos/dados sensíveis em repositório público.


## Arquivos identificados para o primeiro ensaio (04/11/2026)

O operador informou que as fotografias estão **no computador local**, no diretório `~/Downloads/WhatsApp Unknown 2026-10-20 at 16.21.03/`, e que o arquivo DXF correspondente se encontra em `~/Downloads/`. Uma cópia do DXF intitulada `QUEST 7 - LINGUETA(1).dxf` foi disponibilizada separadamente para inspeção nesta conversa, **não no GitHub**.

**Inspeção estrutural realizada somente na cópia anexada, com ezdxf:** arquivo DXF compatível com AutoCAD 2000 (`AC1015`); modelspace com **nove inserções `INSERT`**, referenciando nove blocos com **três entidades `CIRCLE` dentro de cada bloco**; `$INSUNITS=0` (unidades de desenho não especificadas). Isso é consistente com as nove referências e três elementos circulares por referência no relatório antigo, mas **não identifica a numeração correta, não comprova que cada círculo seja um furo passante, não define milímetros nem detecta aberturas físicas na foto**.

**Pendente:** descobrir os nomes exatos dos JPEG/PNG na pasta de fotografias e confirmar a existência/nome do DXF na pasta local do operador; selecionar o **original sem overlays** correspondente e copiar arquivos, sem movê-los, para o ensaio privado. Não criar placeholders para satisfazer `--require-files`.

Comandos seguros, sem cópia nem alteração de dados:

```bash
find "/home/hellen/Downloads/WhatsApp Unknown 2026-10-20 at 16.21.03" -maxdepth 1 -type f \
  \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -printf '%f\n'
find /home/hellen/Downloads -maxdepth 1 -type f -iname "*QUEST*LINGUETA*.dxf" -printf '%f\n'
```

**Situação:** arquivo DXF anexo inspecionado estruturalmente; arquivos reais ainda **não vinculados ao manifesto no computador** e ensaio P0 **não executado**. Evitar publicar DXF/fotos/crops no GitHub.


## Identificação dos arquivos locais — 04/11/2026

O operador confirmou **oito fotografias JPEG** na pasta `~/Downloads/WhatsApp Unknown 2026-10-20 at 16.21.03/` e **um DXF correspondente** com nome `QUEST 7 - LINGUETA.dxf` na pasta `~/Downloads/`. Os nomes originais das fotos incluem imagens de horários 16.20.55, 16.20.56 e 16.20.57, algumas com sufixos numéricos. **Ainda não há evidência de que os arquivos tenham sido copiados para `ensaio-001`**.

**Próxima execução local sugerida:** copiar (não mover) o DXF e os oito JPEGs para `controlvision-dados-privados/ensaio-001`; escolher a fotografia `WhatsApp Image 2026-10-20 at 16.20.56 (1).jpeg` como candidata inicial **apenas após conferir que está sem overlay e corresponde à peça**, ou selecionar outra foto original; preencher `cad_arquivo`, `fotografias` e três registros provisórios `V01`/`V02`/`V03` com `estado_fisico=incerto`, `verificado_fisicamente=false`. Não marcar número/tamanho/revisão do CAD como conhecido até confirmação. Quando o manifesto for atualizado, rodar `python -m app.p0_manifest ... --require-files`, com Python do backend. Esta validação só checa arquivo/estrutura, não verifica dados ópticos ou verdade física.

**Importante:** a cópia do DXF anexada à conversa tinha nome diferente (`QUEST 7 - LINGUETA(1).dxf`); **não foi comprovada igualdade binária entre o anexo e a versão local**. Verificar a estrutura da versão copiada separadamente antes de aproveitar conclusões do anexo. Nenhum dado privado foi versionado.


## Ensaio privado — arquivos vinculados e manifesto aprovado (04/11/2026)

O operador executou `cp -n` do DXF `QUEST 7 - LINGUETA.dxf` e dos JPEGs de Downloads para a pasta privada `controlvision-dados-privados/ensaio-001/{cad,fotos}`. O comando `cp` exibiu **avisos de portabilidade** sobre `-n` (sugere `--update=none`), mas **nenhum erro de cópia**. Em operações posteriores, preferir `cp --update=none` no GNU coreutils para não sobrescrever os originais.

O operador editou o manifesto privado: `peca_fisica_id=LINGUETA_ENSAIO_001`; material, revisão e revisor assinalados como ainda não confirmados; DXF relativo `cad/QUEST 7 - LINGUETA.dxf`; fotografia F01 `fotos/WhatsApp Image 2026-10-20 at 16.20.56 (1).jpeg`, iluminação `outra`, declaração `original_sem_overlay=true` (a inspeção visual desse atributo está **pendente**); geometrias provisórias V01, V02, V03 todas com `estado_fisico=incerto` e `verificado_fisicamente=false`.

**Resultado efetivamente recebido:**

```text
Estrutura P0 válida. NÃO significa vazadores validados nem captura adequada.
Versão DXF: AC1015
Unidades declaradas: 0
Blocos inseridos: 9
```

O arquivo DXF local foi aberto com `ezdxf`; a consulta comprovou a versão, a ausência de unidade declarada e **nove INSERTs no modelspace**. Essa consulta **não contou as entidades circulares dos blocos locais, não estabeleceu numeração e não comprovou equivalência binária** com o DXF anexado anteriormente. `$INSUNITS=0` impede presumir milímetros sem confirmar a unidade de origem.

**Próxima ação:** conferir visualmente F01 sem sobreposições, identificar a revisão e a referência entre os nove blocos, e fazer anotação física dos três vazadores correspondentes. Ainda não existem confirmação individual de furo, teste óptico real calibrado, dataset rotulado, treino de IA ou homologação.
