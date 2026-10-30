@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title PlantView Studio - Preparar dependencias
set "BASEPY="
if exist ".venv\Scripts\python.exe" goto :instalar
where py >nul 2>&1
if not errorlevel 1 (
  py -3.12 -c "import struct; assert struct.calcsize('P')==8" >nul 2>&1
  if not errorlevel 1 set "BASEPY=py -3.12"
)
if not defined BASEPY (
  where python >nul 2>&1
  if not errorlevel 1 (
    python -c "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8" >nul 2>&1
    if not errorlevel 1 set "BASEPY=python"
  )
)
if not defined BASEPY (
  echo [ERRO] Python 3.12 de 64 bits nao encontrado.
  echo Instale de https://www.python.org/downloads/ e habilite Python Launcher.
  exit /b 1
)
echo [1/3] Criando ambiente virtual...
%BASEPY% -m venv ".venv"
if errorlevel 1 exit /b 1
:instalar
if not exist ".venv\Scripts\python.exe" exit /b 1
echo [2/3] Atualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
echo [3/3] Instalando bibliotecas... Requer internet na primeira execucao.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
echo [OK] Dependencias instaladas.
exit /b 0
