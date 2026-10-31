@echo off
setlocal
cd /d "%~dp0"
title PlantView Studio 0.0.2 - Gerador de Instalador
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "build-windows.ps1"
if errorlevel 1 (
    echo.
    echo [ERRO] Ocorreu uma falha durante o build. Verifique as mensagens acima.
    pause
    exit /b 1
)
echo.
echo [CONCLUIDO COM SUCESSO] Pressione qualquer tecla para sair.
pause

