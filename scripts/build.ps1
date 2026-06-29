# Build do PDF Summarizer: PyInstaller (.exe) e, opcionalmente, instalador Inno Setup.
#
# Uso:
#   .\scripts\build.ps1              # só gera dist\PDFSummarizer\
#   .\scripts\build.ps1 -Installer   # gera exe + installer\output\PDFSummarizer-Setup-*.exe

param(
    [switch]$Installer
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"
$PyInstaller = Join-Path $Root ".venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $Python)) {
    Write-Error "Ambiente virtual não encontrado. Crie com: python -m venv .venv"
}

Write-Host "==> Instalando dependências de build..."
& $Pip install -q -r requirements.txt
& $Pip install -q -e .
& $Pip install -q pyinstaller

Write-Host "==> Gerando executável (PyInstaller)..."
& $PyInstaller @(
    "PDFSummarizer.spec",
    "--noconfirm"
)
if ($LASTEXITCODE -ne 0) {
    Write-Error @"
PyInstaller falhou (código $LASTEXITCODE).
Feche o PDFSummarizer.exe se estiver aberto e tente novamente.
"@
}

$DistExe = Join-Path $Root "dist\PDFSummarizer\PDFSummarizer.exe"
if (-not (Test-Path $DistExe)) {
    Write-Error "Build falhou: $DistExe não foi criado."
}

Write-Host "==> Executável pronto: $DistExe"

if (-not $Installer) {
    Write-Host ""
    Write-Host "Para gerar o instalador Windows, execute:"
    Write-Host "  .\scripts\build.ps1 -Installer"
    exit 0
}

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Iscc) {
    Write-Error @"
Inno Setup 6 não encontrado.

Instale em: https://jrsoftware.org/isdl.php
Depois execute novamente: .\scripts\build.ps1 -Installer
"@
}

Write-Host "==> Compilando instalador (Inno Setup)..."
& $Iscc (Join-Path $Root "installer\PDFSummarizer.iss")

$SetupDir = Join-Path $Root "installer\output"
$Setup = Get-ChildItem -Path $SetupDir -Filter "PDFSummarizer-Setup-*.exe" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Setup) {
    Write-Error "Instalador não foi gerado em $SetupDir"
}

Write-Host "==> Instalador pronto: $($Setup.FullName)"
