# SAM 2 opcional no ControlVision — Etapa E1.3

**Situação em 23/10/2026:** executor preparado, **desativado por padrão**, sem
pesos no repositório, sem dependências pesadas no `backend/requirements.txt`
e **sem teste de inferência com modelo real**. Os testes automatizados usam
predições simuladas; eles não medem qualidade de segmentação.

## Por que um executor opcional?

O reconhecimento de silhuetas com SAM 2 é um **experimento**. A aplicação
existente (`/api/vision/preview` e validação de vazadores) segue em OpenCV
mesmo quando SAM 2 estiver instalado. As referências CAD, a numeração e as
medidas físicas não são modificadas pela IA.

A rota exclusiva `POST /api/vision/segmentation/preview` aceita
`method=opencv` (padrão) ou `method=sam2`. Para `method=sam2`:

1. Verifica **explicitamente** `CONTROLVISION_SAM2_ENABLED=1`.
2. Valida variante, caminho de checkpoint existente e dispositivo.
3. Localiza o contorno pelo OpenCV e transforma a silhueta em **prompt de
   caixa**; isso **não** é uma detecção inteiramente independente de OpenCV.
4. Importa `torch` e `sam2` **somente nesse momento**.
5. Executa `SAM2ImagePredictor.set_image` e `predict(box=..., multimask_output=False)`.
6. Obtém a maior silhueta externa, preenche essa região e devolve o **contrato
   de máscara v1** (`docs/SEGMENTACAO_CONTRATO.md`).
7. Se não puder executar ou se a máscara for implausível, devolve
   **`indisponivel` ou `inconclusivo`, nunca uma máscara OpenCV fingindo ser IA**.

A inferência é transferida para uma **thread** (e protegida por lock, já que o
predictor mantém estado por imagem). **Não é isolamento de processo**: o modelo
ainda consome RAM/GPU do servidor de laboratório quando ativado. Reservar
separação em processo/serviço para um ensaio posterior, se necessário.

## Configuração para teste local futuro (Etapa 2)

O SAM 2 oficial requer Python >= 3.10, PyTorch >= 2.5.1 e torchvision >=
0.20.1, além dos seus modelos/checkpoints. Consulte a documentação oficial
antes de instalar (versões e requisitos podem mudar):

- https://github.com/facebookresearch/sam2
- https://github.com/facebookresearch/sam2/blob/main/INSTALL.md

**Não execute instalação dos modelos na rotina normal do ControlVision.**
Use um ambiente de laboratório separado com CPU/GPU adequada; a instalação
do `sam2` é adicional à do backend habitual. O SAM 2 é um modelo pesado,
e no modo CPU pode ser lento; GPU CUDA só se houver suporte e memória.

Configurações possíveis:

| Variável | Exemplo | Significado |
|---|---|---|
| `CONTROLVISION_SAM2_ENABLED` | `1` | Habilita **explicitamente** o modelo; ausente/desigual a 1 mantém desativado |
| `CONTROLVISION_SAM2_VARIANT` | `tiny` | `tiny`, `small`, `base_plus` ou `large` |
| `CONTROLVISION_SAM2_CHECKPOINT` | `/caminho/privado/sam2.1_hiera_tiny.pt` | Checkpoint local correspondente à variante, sem baixar automaticamente |
| `CONTROLVISION_SAM2_DEVICE` | `cpu` | `cpu` (padrão) ou `cuda` |

As configurações oficiais correspondentes são escolhidas por variante
(`configs/sam2.1/sam2.1_hiera_t.yaml`, `_s.yaml`, `_b+.yaml`, `_l.yaml`).
Os pesos devem **corresponder à configuração escolhida**; a extensão e
o nome do arquivo não bastam para demonstrar compatibilidade.

Exemplo de requisição **com SAM 2 desativado** (não precisa instalar IA):

```bash
curl -X POST http://127.0.0.1:8000/api/vision/segmentation/preview \
  -F "file=@/caminho/privado/foto.jpg" \
  -F "method=sam2" -F "mode=holes" -F "piece_tone=light"
```

O retorno normal sem habilitação é similar a:

```json
{
  "schema_version": "1.0",
  "status": "indisponivel",
  "method": "sam2_optional",
  "mask_png_base64": null,
  "contour_px": [],
  "foreground_pixels": 0,
  "prompt_used": false,
  "calibrated": false,
  "requires_human_review": true
}
```

**Os demais campos seguem o contrato completo v1; esta resposta é somente
um exemplo parcial.** A API responde HTTP 200 para estados do diagnóstico
(`indisponivel`/`inconclusivo`), HTTP 422 para método desconhecido, imagem
inválida ou parâmetros inválidos e HTTP 413 para upload acima de 15 MB.

## Salvaguardas e limites

- **Nunca subir** pesos/checkpoints, máscaras anotadas, fotografias reais ou CADs
  privados ao GitHub público. O `.gitignore` ignora extensões de checkpoints e
  diretórios privados, mas é necessário verificar `git status` antes do commit.
- Não são utilizados rótulos de vazadores nem marcações manuais como verdade
  para fabricar uma máscara ou aumentar artificialmente os resultados.
- O prompt é uma caixa obtida pela **heurística atual**; se o OpenCV não
  localizar a peça, o SAM 2 **não é executado** nesse fluxo. Essa limitação
  deve entrar na avaliação de E2.
- A segmentação retornada representa a **silhueta externa preenchida**;
  pequenos vazadores internos continuam fora do escopo.
- Sem medição px/mm, inferência de numeração, decisão dimensional ou aprovação.
- O checkpoint informado pelo operador será **carregado somente sob opt-in**
  e o modelo é mantido em memória para próximas requisições de laboratório.
- A validação de qualidade das máscaras **não foi realizada**; a comparação
  SAM 2 vs. OpenCV exige máscaras de referência revisadas e fotos novas.

## Testes e próximos passos

`backend/tests/test_sam2_optional.py` cobre estados desativado/sem pesos,
configuração inválida, dependências ausentes, falha na inferência, máscaras
simuladas válidas e inválidas, preservação da API OpenCV existente e serialização
do contrato compartilhado.

**E1.4 (próxima):** mostrar máscaras OpenCV/SAM 2 lado a lado no Vue,
inclusive estados indisponível/inconclusivo, sem afirmar que a inferência real
já foi validada. E1.5 será encerrada somente após os testes complementares
de interface e o ensaio de E2 com dependências/pesos locais.
