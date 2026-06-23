# 1 Instalando WSL2 com Ubunto_24.04 no windows

## Verificando versões disponiveis 

No Powershell do Windows

```bash
wsl --list --online
```
## Instalando Ubundo 24.04

```bash
wsl --install -d Ubuntu-24.04
```

- Após instalar configurar usuário ADM e SENHA 
  
  ## Verificar a versão instalada

```bash
wsl -l -v
```

Se quiser deixar como padrão essa versão do Ubunto no WSL

```bash
wsl --set-default Ubuntu-24.04
```

# 2 Python

## Atualizar os Pacotes do Sistema (exige senha)

```bash
sudo apt update && sudo apt upgrade -y
```

## Gerenciador de pacotes `pip` e modulo para ambientes virtuais `venv`

Precisa de Python na versão 3 pra rodar.

```bash
sudo apt install python3 python3-pip python3-venv -y
```

## Verificar as Instalações

```bash
python3 --version
pip3 --version
```

## Criando ambiente virtual (separando libs do projeto das libs do sistema)

Navegue até a pasta do seu projeto (ex: cd cd /mnt/c/meu-projeto).

```bash
cd /mnt/c/GIT/ZAPFCOORP/py-rag-local-bot
```

## Crie o ambiente virtual:

```bash
python3 -m venv .venv
```

## Ative o ambiente: (Vai mostrar o .venv no terminal)

```bash
source .venv/bin/activate
```

## Instalando as Libs necessárias

```bash
pip install pdfplumber
```

## Teste a Instalação

```bash
python3 -c 'import pdfplumber; print("PDFPlumber instalado com sucesso!")'
```

# 3 Instalando Ollama com Phi3

## Instale o curl (se ainda não tiver)

```bash
sudo apt install curl -y
```

## Instale o Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Verifique a instalação e versão do Ollama

```bash
ollama --version
```

## Baixe o Phi3

```bash
ollama pull phi3
```

## Testand o Phi3 no Ollama

```bash
ollama run phi3 "Poderia resumi textos para mim?"
```

# 4 Rodando a aplicação com LLM Local

## Extrair textos de PDF

Ler os PDFs na pasta `pdfs` e criar um arquivo `.txt` com o mesmo nome na pasta `resultados`

```bash
python3 pdf_extractor.py pdfs/
```

## Sumarizar os textos e criar resumos na pasta `resumos`

```bash
python3 summarize.py pdfs/
```

## Parar o serviço

```bash
sudo systemctl stop ollama.service
```

## Verificar status
```bash
sudo systemctl status ollama.service
```