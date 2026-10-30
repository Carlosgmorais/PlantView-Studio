$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Instale Python 3.12 x64 de python.org e tente novamente.' }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias.' }
Write-Host 'Pronto. Execute iniciar.cmd ou build-windows.ps1.'
