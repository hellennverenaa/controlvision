# E1.6 — Protocolo experimental de avaliação de segmentação

**Data: 03/11/2026 · Sem homologação industrial.**
**Status:** implementação de métricas e avaliação opt-in. Nenhuma máscara
humana revisada de produção foi medida nesta entrega; os testes são sintéticos.

## 1. Pergunta de avaliação

Quão próxima a **silhueta externa preenchida** extraída de uma fotografia
fica de uma **máscara de referência criada/corrigida e revisada por uma pessoa**,
nas condições de captura conhecidas?

Esta avaliação **não mede vazadores, tamanhos, posições no CAD ou erro de
corte em milímetros**. Uma máscara produzida automaticamente pelo OpenCV,
por IA ou projetada do CAD **não pode servir como referência humana apenas
porque parece visualmente correta**. Caso a mesma máscara avaliada seja
fornecida como referência, os indicadores ficam artificialmente perfeitos;
a API não pode verificar a honestidade dessa revisão, por isso exige a
confirmação explícita do operador.

## 2. Entrada e fluxo

Na Etapa 3 da interface, após carregar uma fotografia:

1. Use **Comparar máscaras da fotografia** para visualizar as silhuetas
   sem avaliação de desempenho.
2. Crie ou corrija externamente uma máscara da **silhueta externa inteira**,
   com cuidado nas bordas. A ferramenta de anotação será aprimorada na E3.
3. Salve o resultado **em PNG 8-bit, apenas um canal (grayscale), 0 para
   fundo e 255 para peça**. Mesmo tamanho, orientação e enquadramento exatos
   da fotografia original. A máscara deve conter peça **e** fundo.
4. Clique em **Selecionar máscara revisada (PNG)**, marque
   **Confirmo que revisei manualmente o contorno desta peça** e pressione
   **Avaliar contra referência revisada**.
5. Veja métricas separadas por método, tempo de processamento e motivos
   de avaliação indisponível. A UI **não** calcula métricas sem a referência.

### API

`POST /api/vision/segmentation/evaluate`, multipart/form-data:

| Campo | Conteúdo | Obrigatório |
|---|---|---|
| `file` | Foto original (até 15 MB) | Sim |
| `reference_mask` | PNG binário revisado (até 15 MB) | Sim |
| `reference_reviewed` | `true`, declaração humana explícita | Sim |
| `mode` | `holes` ou `marks`, padrão `holes` | Não |
| `piece_tone` | `light` ou `dark`, padrão `light` | Não |

A API **reexecuta** OpenCV e SAM 2 opcional na mesma fotografia e mesma
configuração, independentemente da visualização anterior. O SAM 2 permanece
desativado por padrão. O limite provisório deste módulo é **8 megapixels**;
a API rejeita imagens acima dele, máscaras não binárias, PNG colorido,
fundo/peça vazios, dimensões diferentes ou ausência de revisão declarada.
Não há reajuste automático de escala, perspectiva, alinhamento ou tamanho.
Não há persistência de fotografias ou máscaras.

Resultado exemplar abreviado (valores somente estruturais):

```json
{
  "status": "experimental",
  "units": "pixels_nao_calibrados",
  "reference": {
    "human_review_declared": true,
    "source": "png_binario_externo_revisado_pelo_operador",
    "image_size_px": [200, 160],
    "foreground_pixels": 10101
  },
  "methods": {
    "opencv": {
      "segmentation_status": "ok",
      "evaluation_status": "avaliado",
      "metrics": {
        "iou": 1.0,
        "dice": 1.0,
        "boundary_mean_px": 0.0,
        "boundary_p95_px": 0.0
      },
      "elapsed_ms": 22.12
    },
    "sam2": {
      "segmentation_status": "indisponivel",
      "evaluation_status": "nao_medido",
      "metrics": null,
      "elapsed_ms": 0.4
    }
  }
}
```

**Os valores acima não são de um ensaio real.** Todos os outros campos e avisos
fazem parte do retorno completo. A ausência de previsão de um método **não
corresponde a IoU 0**; é `nao_medido`. As falhas de segmentação devem ser
contabilizadas separadamente, como parte das futuras avaliações por lote.

## 3. Definição matemática das métricas

Considere `R` = pixels brancos da referência humana,
`P` = pixels brancos da predição, ambos na **mesma grade de pixels**.

- **IoU** = `|R ∩ P| / |R ∪ P|`, escala 0 a 1.
- **Dice** = `2 |R ∩ P| / (|R| + |P|)`, escala 0 a 1.
- **Erro médio da borda (px):** média das distâncias euclidianas dos pixels
  de borda de `R` até a borda de `P` **e vice-versa**. A borda de cada
  máscara é o conjunto dos pixels da silhueta removidos por uma erosão de
  3×3 pixels. O distanciamento usa `cv2.distanceTransform` com `DIST_L2`
  e `DIST_MASK_PRECISE`.
- **Erro p95 da borda (px):** percentil 95 dessa coleção **simétrica**
  de distâncias. **Não é distância de Hausdorff máxima.**
- **Tempo (ms):** `elapsed_ms` retornado pelo algoritmo, sem transporte,
  upload, exportação PNG ou renderização. Repetir medições várias vezes para
  comparar desempenho, pois a primeira inicialização do modelo é mais lenta.

Casos sem máscara válida do algoritmo: `evaluation_status=nao_medido` e
`metrics=null`; `segmentation_status` preserva
`indisponivel`/`inconclusivo`, sem mascará-lo como "erro de contorno".
A referência humana deve conter peça e fundo; casos com referência vazia ou
totalmente branca são rejeitados como **entrada inválida**, não tratados como
uma previsão perfeita.

## 4. Protocolo para comparar modelos nas próximas etapas

- **Congelar a versão do dataset e os rótulos** revisados independentemente.
  Separar treino/validação/teste por **peça física**, não por rotações da
  mesma foto.
- Registrar por fotografia: identificador privado, peça física, material,
  iluminação, resolução e método/checkpoint, `prompt_used`, estado de
  segmentação, IoU/Dice, borda média/p95, tempo, hardware e exceções.
- Avaliar o **mesmo conjunto de fotografias** para ambos os métodos, sem
  omitir imagens em que um falhou. Contabilizar as indisponibilidades,
  segmentações inconclusivas e falhas como **taxas separadas**.
- Reportar mediana, p95 e amplitude por material/condição quando houver
  amostra suficiente. **Não** reportar "acurácia industrial" a partir de
  um único exemplo ou de casos sintéticos.
- O SAM 2 recebe caixa originada do OpenCV: é um experimento **assistido**,
  não uma demonstração de independência da IA.
- A ausência de medidas calibradas implica que todos os erros de borda
  são expressos em **pixels**, nunca convertidos para mm.
- Nenhum critério de aceitação/reprovação foi definido com Qualidade.

## 5. Privacidade e validação

O repositório GitHub é público: **não** publicar fotos reais, CADs da fábrica,
PNG de referência revisados ou checkpoints de modelos. O backend só processa
os arquivos na memória durante a requisição e não grava um dataset.

**Testes sintéticos:** `backend/tests/test_segmentation_evaluation.py`
valida identidade (IoU/Dice 1 e borda 0), deslocamento, ausência de
sobreposição, máscaras não binárias, formatos e dimensões, solicitação
sem revisão, avaliação OpenCV/IA desligada e falha de previsão.

**Limitação reconhecida:** a caixa de seleção indica declaração humana de
revisão; a aplicação não pode verificar se a máscara foi criada de fato por
uma pessoa. Uma futura etapa de anotação com auditoria ajudará a organizar
essa evidência.

**Próximo passo:** E2.1, verificar requisitos/licenças/checkpoints SAM 2
e preparar um primeiro ensaio **real** controlado; E3 organizará as máscaras
revisadas para comparação estatística.
