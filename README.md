# ControlVision

**Protótipo experimental de inspeção geométrica de peças cortadas. NÃO HOMOLOGADO para liberar produção.**

Sistema web que importa DXF e HPGL/PLT, identifica peças candidatas e seus contornos internos, permite selecionar uma peça pela lista ou clicando no desenho e analisa experimentalmente fotografias ou webcam. A classificação interna pode ser revista pelo operador.

## Tecnologias

- Vue 3 + TypeScript + Vite no frontend.
- Python + FastAPI, ezdxf, Shapely e OpenCV no backend.
- PostgreSQL, auth corporativa, PM2 e API Gateway: integrações posteriores, após validação.

## Executar localmente

Backend (Python 3.11 ou superior):

    cd backend
    python -m venv .venv
    # Linux: source .venv/bin/activate
    # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Frontend (Node 20+):

    cd frontend
    npm install
    npm run dev

Abrir http://localhost:5173; Vite encaminha chamadas /api ao FastAPI local.

Testes automatizados:

    cd backend
    pip install pytest
    python -m pytest -q

## Roteiro de validação

1. Importar um DXF com uma peça e outro com várias peças e numerações.
2. Confirmar cada contorno no desenho e na lista de seleção.
3. Verificar círculos e recortes internos; marcar provisoriamente como vazador, referência ou ignorar.
4. Importar o HPGL equivalente e observar diferenças de agrupamento.
5. Enviar uma imagem ou usar a webcam apenas para inspecionar a extração visual de contorno.


## Fluxo guiado de teste (atualização)

1. **Importar CAD** e escolher uma peça pela lista ou pelo desenho.
2. **Conferir geometrias internas.** O programa destaca círculos com marcadores maiores, apenas para visualização. Um círculo interno recebe a sugestão de "possível vazador", mas a função precisa ser confirmada por alguém que conheça o molde.
3. **Testar imagem.** Envie uma fotografia ou use a webcam, de preferência com uma peça realmente recortada, plana e em fundo contrastante. O contorno vermelho é somente o contorno detectado em pixels.
4. **Comparação dimensional CAD x peça** ainda está indisponível: faltam alinhamento rígido, calibração, medição dos vazadores e testes metrológicos.

Uma fotografia de **um contorno desenhado com caneta sobre uma folha de papel** não permite testar a identificação dos vazadores físicos, já que eles não estão recortados. Os contornos brutos encontrados pela segmentação incluem ruídos e não indicam quantidade de defeitos.

Os dados de classificação da etapa 2 não são gravados, e a confirmação visual não autoriza uso industrial.

## Limites conhecidos

- Nenhuma aprovação/reprovação automática de produção.
- Sem calibração óptica nem comparação CAD x fotografia em milímetros.
- Sem tolerâncias definidas ou metrologia validada.
- O importador pode gerar candidatos falsos. Todos devem ser revisados.
- Camadas do DXF não são usadas como classificação definitiva de contorno e furo.
- DXFs podem não declarar unidade de medida; a escala HPGL usada é hipótese de 40 unidades/mm.
- O upload não persiste no servidor; classificações não persistem após recarregar a página.
- Os CADs reais da fábrica NÃO foram colocados no repositório público.
- Limite experimental de 20 MB por CAD e 15 MB por fotografia.

Consulte docs/VALIDACAO.md.

## Crédito / licenças

Implementação nova; o projeto SeAMKedu/dxf_contour_comparer foi consultado como referência, mas não teve seu código copiado por ausência de licença explícita. Respeitar licenças das dependências.
