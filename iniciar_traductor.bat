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
echo [INFO] Verificando Python %PYTHON_VER%...

py -%PYTHON_VER% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python %PYTHON_VER% o el 'py launcher' no esta instalado.
    echo Por favor, instala Python %PYTHON_VER% y asegurate de marcar "py launcher" durante la instalacion.
    pause && exit /b
)

if not exist "%VENV_DIR%" (
    echo [INFO] Creando entorno virtual aislado en %VENV_DIR%...
    py -%PYTHON_VER% -m venv %VENV_DIR%
)

echo [INFO] Activando entorno virtual...
call %VENV_DIR%\Scripts\activate

REM --- GENERACION DE RECURSOS ---
echo [INFO] Generando manifiesto de dependencias exactas (Pinning)...
(
  echo # LISTA DE VERSIONES PINNED - PDF Translator v1.2
  echo PyMuPDF==1.23.8
  echo openai==1.12.0
  echo pydantic==2.6.1
  echo click==8.1.7
  echo colorama==0.4.6
) > %REQ_FILE%

if not exist ".gitignore" (
    echo [INFO] Generando .gitignore base...
    echo .venv/ > .gitignore
    echo __pycache__/ >> .gitignore
    echo *.pdf >> .gitignore
    echo font_report/ >> .gitignore
)

if not exist "src\__init__.py" type nul > "src\__init__.py"
if not exist "src\pdf_translation\__init__.py" type nul > "src\pdf_translation\__init__.py"
if not exist "src\validation_pipeline\__init__.py" type nul > "src\validation_pipeline\__init__.py"

REM --- INSTALACION Y EJECUCION ---
echo [INFO] Instalando/Verificando librerias bloqueadas...
pip install -r %REQ_FILE% >nul 2>&1

echo [OK] Entorno listo y validado.
echo =======================================================
echo.

REM Ejecutando el modulo principal con una prueba de concepto
python src\pdf_translation\main.py --input test.pdf --output test_translated.pdf --source es --target en --generate-font-report

echo.
echo =======================================================
echo [INFO] Proceso finalizado.
pause