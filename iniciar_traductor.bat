@echo off
setlocal enabledelayedexpansion
title PDF Translator v1.2 - Entorno de Ejecucion

REM --- CONFIGURACION DEL ENTORNO ---
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

REM --- GENERACION DE DEPENDENCIAS ---
(
  echo PyMuPDF==1.23.8
  echo openai==1.35.0
  echo httpx==0.27.2
  echo pydantic==2.6.1
  echo colorama==0.4.6
  echo requests==2.31.0
  echo PySide6==6.6.2
) > %REQ_FILE%

pip install -r %REQ_FILE% >nul 2>&1

REM --- EJECUCION DEL SISTEMA ---
echo [OK] Entorno listo. Iniciando Interfaz Grafica...
echo =======================================================
echo.

REM Lanzamos la app. Los idiomas por defecto seran Ingles a Español, 
REM y el programa pedira el archivo PDF graficamente.
python src\pdf_translation\main.py --source English --target Spanish

echo.
echo =======================================================
echo [INFO] Proceso finalizado.
pause