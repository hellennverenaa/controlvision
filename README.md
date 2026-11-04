# ControlVision

**Status: protótipo experimental — não homologado para aprovar ou liberar peças na produção.**

O **ControlVision** é uma aplicação web de inspeção de peças cortadas para calçados. Sua finalidade é associar uma peça física fotografada à referência **CAD correta** (modelo/numeração quando identificáveis) e investigar **vazadores passantes minúsculos**, recortes e possíveis falhas de corte. As malhas podem ter tramas que parecem furos; a inspeção precisa distinguir textura normal de aberturas produzidas pela máquina.

**Cenário previsto:** vários computadores na produção acessam o sistema pelo navegador; a cabine física já existe, mas a **câmera fixa ainda não foi escolhida nem instalada**. Os modelos de IA deverão operar em serviço central, não em cada posto. Isso é **direção de arquitetura**, não recurso disponível hoje.

## Funcionalidades existentes (branch `feat/prototipo-validacao`)

- Importação experimental DXF e HPGL/PLT/HP2, visualização e seleção de peças; classificação humana de geometrias internas.
- Upload/webcam e segmentação preliminar de silhueta com OpenCV; opções de peça clara/escura.
- Prévia visual de correspondência CAD × foto, inclusive múltiplas referências com numeração desconhecida.
- Candidatos ópticos, inspeção assistida de regiões CAD, anotações manuais e diagnósticos de microcontraste.
- Laboratório de máscaras OpenCV × SAM 2 **opcional** e cálculo de IoU/Dice apenas com máscara externa revisada por pessoa.
- Testes sintéticos no backend e no frontend; GitHub Actions.

**Ainda não existe:** reconhecimento confiável e automático da referência CAD, IA treinada para diferenciar trama e vazador, segmentação SAM 2 real comprovada, calibração dimensional em mm, homologação industrial, banco PostgreSQL, autenticação corporativa ou implantação web multiusuário.

**Evidência anterior:** uma lingueta branca sobre fundo azul produziu máscara externa visualmente plausível; o detector encontrou **15 candidatos circulares** frente a três entidades circulares por referência CAD. Candidatos **não** equivalem a furos físicos. Ver [evidências anteriores](docs/EVIDENCIAS_TESTES_LINGUETA_ANTERIORES.md).

## Tecnologias

Frontend Vue 3 + TypeScript + Vite; backend Python + FastAPI + OpenCV + ezdxf + Shapely + NumPy. SAM 2 está presente **somente como integração experimental opcional**; treinamento e serviço central de IA são futuros.

## Executar protótipo local

Requisitos: Node.js 20+ e Python compatível com as dependências da aplicação. **O laboratório Python 3.12 para IA é separado do backend da aplicação.**

Na raiz do projeto, instale o backend se necessário:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install pytest
cd ..
```

Após `npm install` na raiz, em dois terminais (na raiz):

```bash
npm run backend
# Em outro terminal:
npm run frontend
```

Acesse `http://localhost:5173`. O Vite encaminha `/api` à API local `http://127.0.0.1:8000`. Execução local **não equivale a implantação corporativa**.

Verificações:

```bash
cd backend && .venv/bin/python -m pytest -q
# em outro terminal:
cd frontend && npm install && npm run build
```

O build frontend inclui testes da comparação de máscaras. Confira também o GitHub Actions da branch; não presuma que testes de câmera real foram realizados.

## Documentação oficial do projeto

**Comece por [Índice da documentação](docs/README.md)**, [Requisitos do produto](docs/REQUISITOS_PRODUTO.md), [Arquitetura e fluxos](docs/ARQUITETURA_SISTEMA.md) e [Plano de desenvolvimento](PLANO_DESENVOLVIMENTO.md).

A documentação de experimentos permanece separada. Não envie fotos de fábrica, moldes proprietários, checkpoints ou dados sensíveis ao GitHub público. **Sem aprovação/reprovação industrial enquanto não houver validação física, óptica, metrológica e critérios da Qualidade.**

**Branch de desenvolvimento:** `feat/prototipo-validacao` (PR #1 em rascunho); `main` ainda não recebeu o protótipo.
