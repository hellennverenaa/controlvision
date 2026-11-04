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
