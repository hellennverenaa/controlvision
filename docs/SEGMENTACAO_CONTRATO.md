# Contrato de segmentação v1 — ControlVision (E1.1)

**Estado:** baseline OpenCV funcional + **executor opcional SAM 2 conectado (E1.3)**. Dependências e pesos **não são instalados automaticamente**, e **não houve execução real do modelo nem avaliação de imagens reais**. U-Net ainda não implementada.
Este contrato **não altera** as rotas existentes de inspeção `/api/vision/preview`
e `/api/vision/manual-regions`.

## Objetivo

Garantir que a silhueta extraída por OpenCV e por uma futura IA tenha **a mesma
representação de saída**. Trata-se da **máscara da silhueta externa** da peça;
os pequenos furos internos **não** são o alvo nesta etapa. O contrato NÃO
autoriza conclusão de conformidade, medida em milímetros ou identificação de numeração.

## Endpoint opcional

`POST /api/vision/segmentation/preview` — corpo `multipart/form-data`:

| Campo | Valor | Padrão |
|---|---|---|
| `file` | Fotografia JPG/PNG válida (até 15 MB) | obrigatório |
| `method` | `opencv` ou `sam2` | `opencv` |
| `mode` | `holes` ou `marks` | `holes` |
| `piece_tone` | `light` ou `dark` | `light` |

`method=sam2` chama somente o executor opcional. Como SAM 2 permanece desativado por padrão, a resposta é **HTTP 200 com `status=indisponivel`**, `mask_png_base64=null`, `method=sam2_optional` e aviso explícito. Para ativação local, requer flag, pesos e dependências; sem eles, segue indisponível. Métodos desconhecidos retornam **HTTP 422**. Não há fallback silencioso para OpenCV. Ver `docs/SAM2_EXECUCAO_EXPERIMENTAL.md`.

## JSON de saída

```json
{
  "schema_version": "1.0",
  "status": "ok",
  "method": "opencv_baseline",
  "model_version": null,
  "prompt_used": false,
  "image_size_px": [480, 360],
  "mask_mime_type": "image/png",
  "mask_png_base64": "<dados PNG binários codificados em base64>",
  "mask_origin": "poligono_externo_preenchido_do_opencv_atual",
  "contour_px": [[90, 60], [380, 60], [380, 290], [90, 290]],
  "foreground_pixels": 67300,
  "elapsed_ms": 25.5,
  "units": "pixels_nao_calibrados",
  "calibrated": false,
  "requires_human_review": true,
  "warnings": ["..."]
}
```

**Os números acima são exemplos da estrutura e não medições de uma foto real.**

- `status`: `ok`, `inconclusivo` ou `indisponivel`. No estado
  `inconclusivo`/`indisponivel`, `mask_png_base64=null`,
  `contour_px=[]` e `foreground_pixels=0`: **nenhuma máscara fictícia**.
- `image_size_px=[largura, altura]`; a máscara PNG tem exatamente essa
  resolução; fundo = 0, silhueta = 255, `uint8`.
- `mask_origin`: rastreabilidade do método usado para criar a máscara.
- `contour_px`: pontos do contorno externo, no sistema da imagem
  (origem no canto superior esquerdo; y aumenta para baixo).
- `elapsed_ms`: tempo do processamento OpenCV, **sem upload ou codificação
  PNG**. A comparação com IA deverá usar medição equivalente. Não é o tempo de
  resposta de ponta a ponta da API.
- `prompt_used`: permitirá distinguir máscaras de IA sem intervenção humana
  de segmentações assistidas por clique/caixa.
- `model_version`: `null` no OpenCV; deve conter versão/checkpoint
  verificável quando houver pesos de IA.
- `requires_human_review=true` e `calibrated=false` na fase atual.

**Importante:** a máscara OpenCV do baseline é obtida preenchendo o
**polígono externo aproximado que o sistema atual já produz**. Portanto,
ela **não é** a máscara bruta de limiarização, e as aberturas internas
ficam preenchidas intencionalmente. Usar o mesmo conceito de silhueta
externa para comparar com modelos futuros.

## Exemplo local

Depois de iniciar o backend, na pasta do projeto:

```bash
curl -X POST http://127.0.0.1:8000/api/vision/segmentation/preview \
  -F "file=@/caminho/privado/para/foto.jpg" \
  -F "method=opencv" -F "mode=holes" -F "piece_tone=light"
```

O retorno inclui a imagem da máscara codificada em PNG/base64. **Não salvar
fotos reais, máscaras proprietárias nem pesos treinados no GitHub público.**

## Verificação e evolução

- `backend/tests/test_segmentation_contract.py`: máscara binária, dimensões,
  serialização PNG, captura inconclusiva, validação de contrato, endpoint
  experimental e regressão do detector atual.
- **E1.2:** preservar OpenCV como padrão; nenhuma rota anterior alterada.
- **E1.3 (conectada):** executor de IA opt-in em `backend/app/sam2_optional.py`. O SAM 2 utiliza **uma caixa derivada do contorno OpenCV** como prompt; logo a comparação futura **não será independente**. A execução ocorre em uma thread de trabalho da API, mas não em um processo separado; isolamento de processo ainda não foi implementado. A evidência de execução com pesos reais permanece pendente para E2.
- **E1.4 (interface implementada):** na Etapa 3 da aplicação Vue, após analisar uma fotografia, clique em **Comparar máscaras da fotografia**. A interface consulta `POST /api/vision/segmentation/preview` com `method=opencv` e `method=sam2` usando **o mesmo arquivo e tom selecionado**, e apresenta lado a lado **fotografia sem sobreposição**, **máscara OpenCV** e **máscara SAM 2**. Se o SAM 2 estiver desativado ou falhar, o painel exibe `indisponivel`/`inconclusivo` com o aviso, sem imagem inventada. A comparação é manual (opt-in), não altera o processamento padrão e descarta respostas antigas quando a fotografia, tom ou molde mudam. A compilação TypeScript/Vue passou; **não foram avaliadas máscaras reais do SAM 2**.
- **E1.5 (testes de integração simulada concluídos):** `backend/tests/test_sam2_optional.py` e `backend/tests/test_segmentation_contract.py` verificam o contrato, dependências/pesos ausentes e regressão OpenCV. `frontend/tests/segmentation-comparison.test.mjs` acrescenta **12 testes automatizados** de transporte, identidade do método, cabeçalho/dimensões PNG, estados indisponível/inconclusivo, erro parcial, rede, JSON inválido e invalidação de respostas antigas. `npm run build` executa **primeiro** `npm run test:comparison` e depois `vue-tsc`/Vite. Testes frontend usam respostas simuladas e **não** validam a qualidade visual do SAM 2; a execução de pesos reais e a avaliação em máscaras humanas continuam previstas na E2/E3. O verificador do frontend inspeciona somente o **cabeçalho/dimensões** do PNG; a integridade completa da imagem é responsabilidade da API e do navegador.
- **E1.6:** definir protocolo IoU/Dice, erro de borda, latência e falhas
  com máscaras humanas revisadas.

Este documento é referência técnica da **ETAPA 1**.
Acompanhar o progresso em `PLANO_DESENVOLVIMENTO.md`.
