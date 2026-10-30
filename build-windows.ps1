$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { & .\setup-windows.ps1 }
if (-not (Test-Path 'engine\plantview-dwg.exe')) {
    cargo build --release --manifest-path dwg-reader/Cargo.toml
    if ($LASTEXITCODE -ne 0) { throw 'Falha no leitor DWG. Instale Rust estavel e as ferramentas de compilacao Windows.' }
    Copy-Item 'dwg-reader\target\release\plantview-dwg.exe' 'engine\plantview-dwg.exe'
}
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm PlantViewStudio.spec
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar o executavel.' }
Write-Host 'Executavel: dist\PlantViewStudio\PlantViewStudio.exe. Distribua a pasta inteira.'
