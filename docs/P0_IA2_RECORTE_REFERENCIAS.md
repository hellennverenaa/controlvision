# P0 / IA 2 — recortes privados para avaliar vazadores e trama

**Data:** 04/11/2026 · **Estado:** ferramenta offline implementada; **nenhum modelo de IA treinado e nenhuma exportação real executada nesta entrega**.

## Objetivo

Construir pares de referência em pixels originais: **microvazadores passantes confirmados por uma pessoa** e **regiões de trama normal revisadas por uma pessoa**. O contraste da fotografia não basta para criar rótulos; a extração não é detector, métrica de desempenho ou treinamento.

O extrator `backend/app/p0_patch_dataset.py` utiliza somente OpenCV e o backend existente; **não precisa de torch/SAM 2**. Lê `manifesto.json` (`p0.1`) e `anotacoes.json` (`p0-patches.1`) privados, grava PNGs em uma subpasta da pasta privada do ensaio. Exige uma fotografia original (`original_sem_overlay=true`), IDs correspondentes, marcações revisadas, confirmação física positiva de cada recorte `vazador_confirmado` e validação de bordas. **Não faz resize** nem fabrica rótulos negativos; não sobrescreve pasta de saída existente. A validação da estrutura não comprova que a anotação humana é verdadeira.

## Primeiro ensaio com lingueta (sem publicar dados)

As três marcações M01/M02/M03 da interface tiveram confirmação física declarada, porém **as coordenadas vêm de uma captura específica**. É necessário conferir que são da **mesma fotografia original F01 de 960 × 1280**, com a mesma orientação e sem qualquer espelhamento/redimensionamento; do contrário não copiar coordenadas para o arquivo privado. A numeração CAD segue não identificada.

1. Atualizar a branch local com cuidado: `git status`, `git switch feat/prototipo-validacao`, `git pull --ff-only origin feat/prototipo-validacao`.
2. No diretório privado `~/Documentos/ambiente_dass/controlvision-dados-privados/ensaio-001/`, criar `anotacoes.json` a partir de `docs/exemplos/p0_anotacoes_sinteticas.json` (copiar e **editar somente a cópia privada**). Alterar o `peca_fisica_id` para corresponder ao manifesto e preencher coordenadas **do original F01 confirmado**.
3. Inserir **M01/M02/M03** como `vazador_confirmado` apenas se o registro de inspeção humana/peça física se aplicar exatamente àquela fotografia. O validador exigirá `revisado_por_pessoa=true` e `existencia_fisica_confirmada=true` para cada positivo. Se não há confirmação, **não incluir como positivo**.
4. Opcional: inserir T01/T02 como `trama_normal_revisada` **apenas após verificar visualmente que são áreas de malha sem vazador**. A ferramenta **não escolherá automaticamente** regiões negativas.
5. Na pasta `backend` executar:

```bash
cd ~/Documentos/ambiente_dass/controlvision/backend
.venv/bin/python -m pytest -q tests/test_p0_patch_dataset.py
.venv/bin/python -m app.p0_patch_dataset \
  ~/Documentos/ambiente_dass/controlvision-dados-privados/ensaio-001/manifesto.json \
  ~/Documentos/ambiente_dass/controlvision-dados-privados/ensaio-001/anotacoes.json \
  --foto-id F01 \
  --saida ~/Documentos/ambiente_dass/controlvision-dados-privados/ensaio-001/patches-v1 \
  --tamanho 64
```

A saída deve conter PNGs `patch_001.png`, etc., e `indice.json` com rótulo declarado, posição no original e ID de anotação; todos são privados. **Não enviar PNGs, índice nem anotações ao GitHub público.** Para repetir, usar nova pasta de saída, nunca sobrepor resultados anteriores.

## Qualidade do dataset e próximo experimento

- Os 3 vazadores da mesma peça **não representam três peças independentes**. Uma avaliação reproduzível de desempenho da IA exige múltiplas peças, materiais, condições de captura e negativos revisados.
- Não treinar nem reportar validação cruzada/accuracy com apenas estes exemplos. Primeiro verificar **integridade dos crops**, qualidade óptica e diferença entre trama e furo em recortes da imagem original.
- Sem revisão positiva de vazadores, a extração de positivos deve parar. Sem negativos revisados, não declarar conjunto binário pronto para treinamento.
- Preservar a referência CAD e futura associação de `cad_feature_id` em sistema privado; coordenadas de foto não são mm nem numeração.
- O próximo experimento poderá comparar medidas ópticas e depois modelos leves supervisionados, separados da IA 1; somente se dados suficientes justificarem.

Referências: [Registro P0](P0_REGISTRO_PRIVADO.md), [Dados e validação](DADOS_TREINAMENTO_VALIDACAO.md), [Plano mestre](../PLANO_DESENVOLVIMENTO.md).


## Execução local informada — 04/11/2026

O operador executou `backend/.venv/bin/python -m pytest -q tests/test_p0_patch_dataset.py` e forneceu:

```text
........ [100%]
8 passed in 0.14s
```

Confirmou também a cópia do exemplo `docs/exemplos/p0_anotacoes_sinteticas.json` para `controlvision-dados-privados/ensaio-001/anotacoes.json` por meio de `cp --update=none`. **A ausência de erro de `cp` não comprova que o arquivo de destino foi substituído, pois a opção não sobrescreve destinos já existentes.** Verificar conteúdo antes de editar.

**Não extrair patches ainda:** as coordenadas do exemplo são sintéticas. É necessário verificar que a fotografia F01 corresponde exatamente à usada nas marcações M01 (825,6; 590,8), M02 (823,7; 719,5) e M03 (240,5; 634,2), além de confirmar as dimensões originais e a relação com o relato físico. Somente então preencher anotações privadas revisadas, sem publicá-las. **Sem exportação real de patches nem modelo treinado.**
