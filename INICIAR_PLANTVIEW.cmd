@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PlantView Studio 0.2 - Inicializacao pelo CMD
set "PV_PY=.venv\Scripts\python.exe"
echo.
echo =======================================================
echo      PlantView Studio 0.2 - Windows CMD
 echo =======================================================
echo.
if not exist "%PV_PY%" (
  echo [INFO] Primeira execucao: preparando ambiente Python...
  call "%~dp0INSTALAR_DEPENDENCIAS.cmd"
  if errorlevel 1 goto :erro
)
if not exist "%PV_PY%" goto :erro
if not exist "engine\plantview-dwg.exe" (
  echo [ERRO] Leitor DWG nao encontrado: engine\plantview-dwg.exe
  echo Extraia o pacote ZIP completo, preservando a estrutura de pastas.
  goto :erro
)
echo [INFO] Iniciando o PlantView Studio...
"%PV_PY%" -c "import PySide6, pyvista, pyvistaqt, cadquery, ifcopenshell, ezdxf"
if errorlevel 1 (
  echo [ERRO] Algumas bibliotecas estao ausentes. Execute INSTALAR_DEPENDENCIAS.cmd.
  goto :erro
)
"%PV_PY%" -u run.py %*
set "PV_EXIT=%ERRORLEVEL%"
if not "%PV_EXIT%"=="0" (
  echo.
  echo [ERRO] Aplicativo encerrou com codigo %PV_EXIT%.
  pause
)
exit /b %PV_EXIT%
:erro
echo.
echo [FALHA] Veja as mensagens acima e execute DIAGNOSTICO.cmd.
pause
exit /b 1
