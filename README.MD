# PDF Summarizer

Aplicação desktop em Python que extrai texto de arquivos PDF e gera resumos estruturados em JSON usando modelos de linguagem (LLM). O projeto unifica três scripts CLI legados em uma arquitetura modular, testável e preparada para empacotamento futuro como executável Windows.

**Repositório:** [ZAPFCOORP/py-rag-local-bot](https://github.com/ZAPFCOORP/py-rag-local-bot)

---

## O que o projeto faz

O PDF Summarizer automatiza um pipeline em duas etapas:

1. **Extração** — lê todos os `.pdf` de uma pasta de entrada e grava o texto extraído em `{pasta_saida}/resultados/{nome}.txt`
2. **Resumo** — envia cada texto à LLM e grava o resultado em `{pasta_saida}/resumos/{nome}.json`

A interface gráfica permite escolher as pastas, configurar o provider de LLM (Ollama local ou OpenRouter), acompanhar o progresso em tempo real e persistir as preferências entre sessões.

```text
Pasta de PDFs          Pasta de saída
     │                       │
     ▼                       ├── resultados/   (*.txt — texto extraído)
  [PDF 1] ──extract──►      │
  [PDF 2] ──extract──►      ├── resumos/      (*.json — resumo estruturado)
     │          │            │
     └──── LLM ◄┘            └── config em %APPDATA%/PDFSummarizer/
```

---

## Arquitetura

O código segue **Separation of Concerns** em camadas distintas, com **Dependency Inversion** no acesso à LLM (Strategy Pattern). O core e os serviços são testáveis sem GUI.

```text
┌─────────────────────────────────────────────────────────┐
│  ui/          CustomTkinter — pastas, provider, log     │
└──────────────────────────┬──────────────────────────────┘
                           │ ProgressEvent callbacks
┌──────────────────────────▼──────────────────────────────┐
│  services/    PipelineService — orquestra o fluxo       │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────────┐
│ core/pdf/     │  │ core/summary/ │  │ infra/providers/  │
│ PdfExtractor  │  │ Summarizer    │  │ OllamaProvider    │
│               │  │ Schema/Parser │  │ OpenRouterProvider│
└───────────────┘  └───────────────┘  └───────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  infra/       ConfigStore, FileSystem                   │
└─────────────────────────────────────────────────────────┘
```

### Decisões de design

| Decisão | Motivo |
|---------|--------|
| **Core desacoplado da UI** | Pipeline testável com pytest; GUI apenas consome eventos de progresso |
| **Strategy Pattern (`LLMProvider`)** | Ollama e OpenRouter compartilham contrato; fácil adicionar novos providers |
| **Fail-soft por arquivo** | Falha em um PDF não interrompe o lote; estatísticas finais indicam sucessos e falhas |
| **Config fora do bundle** | `%APPDATA%/PDFSummarizer/config.json` — compatível com PyInstaller (Fase 1) |
| **Entry point único (`app.py`)** | Um comando para dev e build futuro de `.exe` |
| **TDD desde a Fase 0** | 31 testes automatizados; cobertura ≥ 80% em `core/` e `services/` |

### Estrutura de diretórios

```text
py-rag-local-bot/
├── app.py                      # Entry point da aplicação
├── pyproject.toml              # Metadados e configuração pytest/coverage
├── requirements.txt
├── requirements-dev.txt
├── fase0spec.MD                # Especificação técnica (SDD + TDD)
│
├── src/pdf_summarizer/
│   ├── core/                   # Domínio: modelos, exceções, PDF, schema JSON
│   ├── infra/                  # Config, filesystem, providers LLM
│   ├── services/               # PipelineService (orquestração)
│   └── ui/                     # GUI CustomTkinter
│
├── tests/                      # Unitários + integração (pytest)
├── fixtures/                   # PDFs e textos para testes
└── legacy/                     # Scripts CLI originais (referência)
```

---

## Bibliotecas

| Biblioteca | Uso |
|------------|-----|
| **[pdfplumber](https://github.com/jsvine/pdfplumber)** | Extração de texto de PDFs (páginas concatenadas, UTF-8) |
| **[ollama](https://github.com/ollama/ollama-python)** | Cliente para LLM local via Ollama (`format` JSON schema) |
| **[openai](https://github.com/openai/openai-python)** | Cliente compatível com API OpenRouter (`response_format: json_object`) |
| **[customtkinter](https://github.com/TomSchimansky/CustomTkinter)** | Interface gráfica moderna sobre Tkinter (Windows) |
| **[python-dotenv](https://github.com/theskumar/python-dotenv)** | Carrega `OPENROUTER_API_KEY` do `.env` como fallback |
| **[pytest](https://pytest.org)** + **pytest-cov** + **pytest-mock** | Testes unitários, integração e cobertura (dev) |

### Providers de LLM

- **Ollama (padrão)** — modelo `gemma3:270m`; requer serviço em `http://localhost:11434`; health check antes de processar
- **OpenRouter** — modelo padrão `nvidia/nemotron-3-super-120b-a12b:free`; requer API key (campo mascarado na UI)

Textos longos são truncados automaticamente (8 000 chars Ollama / 10 000 OpenRouter) com aviso no log.

---

## Formato de saída JSON

Cada resumo segue estrutura estável, compatível com saídas anteriores do projeto:

```json
{
  "modelo": "gemma3:270m",
  "requisicao": { "...": "payload enviado à LLM" },
  "resposta": {
    "resumo": "string",
    "pontos_principais": ["string"],
    "informacoes_importantes": ["string"],
    "assuntos": ["string"]
  }
}
```

O campo `assuntos` funciona como tags para busca futura (RAG previsto na Fase 3). Exemplo real: `pdfs/resumos/OR_Profile.json`.

---

## Pré-requisitos

- **Python 3.10+**
- **Windows** (GUI Fase 0; Linux/macOS previstos na Fase 4)
- Para Ollama: [Ollama instalado](https://ollama.com) com modelo baixado (`ollama pull gemma3:270m`)
- Para OpenRouter: conta e API key em [openrouter.ai](https://openrouter.ai)

---

## Instalação e execução

### Windows (recomendado)

```powershell
cd c:\GIT\ZAPFCOORP\py-rag-local-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
python app.py
```

Alternativa equivalente: `python -m pdf_summarizer`

### Linux / WSL (desenvolvimento e testes)

```bash
cd /mnt/c/GIT/ZAPFCOORP/py-rag-local-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
pytest tests/ -v --cov=pdf_summarizer --cov-report=term-missing
```

> A GUI CustomTkinter na Fase 0 é voltada ao Windows. Em WSL, use os testes automatizados; a interface gráfica requer ambiente com display (ou execução nativa no Windows).

---

## Executável e instalador Windows

O app pode ser empacotado como `.exe` (PyInstaller) e instalado como aplicativo Windows (Inno Setup), em `Arquivos de Programas`, com atalhos e desinstalador.

### Pré-requisitos de build

| Ferramenta | Uso | Download |
|------------|-----|----------|
| **Python 3.10+** + venv | Gerar o executável | já usado no desenvolvimento |
| **PyInstaller** | Empacota `dist\PDFSummarizer\` | instalado automaticamente pelo script |
| **Inno Setup 6** | Gera o instalador `.exe` | [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php) |

Instalação rápida do Inno Setup (opcional):

```powershell
winget install --id JRSoftware.InnoSetup -e
```

### Build automatizado (recomendado)

Na raiz do repositório, com o venv ativo ou não:

```powershell
# Apenas executável portátil (pasta dist\PDFSummarizer\)
.\scripts\build.ps1

# Executável + instalador Windows
.\scripts\build.ps1 -Installer
```

**Saídas:**

| Artefato | Caminho |
|----------|---------|
| App portátil | `dist\PDFSummarizer\PDFSummarizer.exe` |
| Instalador | `installer\output\PDFSummarizer-Setup-0.1.0.exe` |

Distribua a pasta `dist\PDFSummarizer\` inteira **ou** o instalador `PDFSummarizer-Setup-*.exe` (recomendado para usuários finais).

### O que o instalador faz

- Copia todos os arquivos para `C:\Program Files\PDFSummarizer\`
- Cria atalho no **Menu Iniciar**
- Opcionalmente atalho na **Área de trabalho**
- Registra desinstalador em **Configurações → Aplicativos**
- Oferece abrir o app ao final da instalação

A configuração do usuário (`%APPDATA%\PDFSummarizer\config.json`) **não** fica na pasta de instalação e é preservada entre atualizações.

> **Ollama não vem no instalador.** O usuário final ainda precisa instalar o [Ollama](https://ollama.com) e baixar o modelo (`ollama pull gemma3:270m`) para usar LLM local.

### Build manual (passo a passo)

```powershell
cd c:\GIT\ZAPFCOORP\py-rag-local-bot
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
pip install pyinstaller

pyinstaller PDFSummarizer.spec
```

Teste: `dist\PDFSummarizer\PDFSummarizer.exe`

> Feche o app antes de rebuildar — arquivos em `dist\` podem ficar bloqueados se o executável estiver em execução.

Com **Inno Setup 6** instalado:

```powershell
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" installer\PDFSummarizer.iss
```

Ou abra `installer\PDFSummarizer.iss` no **Inno Setup Compiler** e compile (Ctrl+F9).

### Arquivos de build no repositório

```text
PDFSummarizer.spec          # Configuração PyInstaller
installer/
  PDFSummarizer.iss         # Script Inno Setup
  output/                   # Instalador gerado (gitignored)
scripts/
  build.ps1                 # Automação build + instalador
```

---

## Configuração

As preferências são salvas automaticamente ao executar ou fechar a aplicação.

| Origem | Prioridade |
|--------|------------|
| Valores da UI (sessão atual) | 1 (mais alta) |
| `%APPDATA%/PDFSummarizer/config.json` | 2 |
| Variável `OPENROUTER_API_KEY` (`.env`) | 3 |
| Defaults hardcoded | 4 |

Exemplo de `config.json`:

```json
{
  "input_dir": "C:/docs/pdfs",
  "output_dir": "C:/docs/saida",
  "provider": "ollama",
  "model": "gemma3:270m",
  "api_key": "",
  "max_chars": 8000
}
```

Para OpenRouter via `.env`, copie `.env-sample` para `.env` e preencha a chave:

```env
OPENROUTER_API_KEY=sua-api-key-aqui
```

A API key **nunca** é registrada em logs.

---

## Testes

```powershell
pip install -r requirements-dev.txt
pytest tests/ -v --cov=pdf_summarizer --cov-report=term-missing
```

| Camada | Escopo |
|--------|--------|
| Unitários | Schema JSON, extração PDF, providers (mock), summarizer, pipeline, config |
| Integração | Pipeline completo PDF → TXT → JSON com LLM mockado |

Gate de qualidade: todos os testes passando; cobertura ≥ 80% em `core/` e `services/`.

---

## Scripts legados

Antes da Fase 0, o fluxo era executado por três scripts independentes na raiz do repositório. Eles foram consolidados no pacote `pdf_summarizer` e permanecem em `legacy/` apenas como referência:

| Script | Função |
|--------|--------|
| `legacy/pdf_extractor.py` | PDF → `.txt` |
| `legacy/summarize.py` | `.txt` → `.json` via Ollama |
| `legacy/summarize-open-router.py` | `.txt` → `.json` via OpenRouter |

**Use `python app.py`** — os scripts legados não são mais mantidos.

---

## Roadmap

| Fase | Entrega |
|------|---------|
| **Fase 0** (atual) | App modular, GUI, testes, config persistente |
| **Fase 1** (em andamento) | PyInstaller, instalador Inno Setup, CI |
| **Fase 2** | Chunking de textos longos, cancelamento, drag-and-drop |
| **Fase 3** | RAG: indexação de `assuntos`, busca local |
| **Fase 4** | Suporte Linux/macOS na GUI |

Detalhes técnicos completos: [`fase0spec.MD`](fase0spec.MD).
