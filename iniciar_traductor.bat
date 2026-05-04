@echo off
setlocal enabledelayedexpansion
title PDF Translator v1.2 - Entorno de Ejecucion

set PYTHON_VER=3.11
set VENV_DIR=.venv
set REQ_FILE=requirements.txt

echo =======================================================
echo   PDF TRANSLATOR V1.2 - INICIALIZACION DE ENTORNO
echo =======================================================

if not exist "%VENV_DIR%" (
    echo [INFO] Creando entorno virtual...
    py -%PYTHON_VER% -m venv %VENV_DIR%
)

call %VENV_DIR%\Scripts\activate

(
  echo PyMuPDF==1.23.8
  echo openai==1.35.0
  echo httpx==0.27.2
  echo pydantic==2.6.1
  echo colorama==0.4.6
  echo requests==2.31.0
  echo PySide6==6.6.2
  echo deep-translator==1.11.4
) > %REQ_FILE%

echo [INFO] Instalando librerias...
pip install -r %REQ_FILE% >nul 2>&1

echo [OK] Entorno listo. Iniciando Interfaz Grafica...
echo =======================================================
echo.

python src\pdf_translation\main.py --source English --target Spanish

echo.
echo =======================================================
pause