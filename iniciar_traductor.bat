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
    echo [ERROR] Instala Python %PYTHON_VER% y el 'py launcher'.
    pause && exit /b
)

if not exist "%VENV_DIR%" (
    echo [INFO] Creando entorno virtual en %VENV_DIR%...
    py -%PYTHON_VER% -m venv %VENV_DIR%
)

call %VENV_DIR%\Scripts\activate

REM --- GENERACION DE RECURSOS Y DEPENDENCIAS ---
echo [INFO] Generando manifiesto de dependencias exactas (Pinning)...
(
  echo # LISTA DE VERSIONES PINNED - PDF Translator v1.2
  echo PyMuPDF==1.23.8
  echo openai==1.12.0
  echo pydantic==2.6.1
  echo colorama==0.4.6
  echo requests==2.31.0
) > %REQ_FILE%

if not exist ".gitignore" (
    echo .venv/ > .gitignore
    echo __pycache__/ >> .gitignore
    echo *.pdf >> .gitignore
)

echo [INFO] Instalando/Verificando librerias bloqueadas...
pip install -r %REQ_FILE% >nul 2>&1

REM --- GENERAR PDF DE PRUEBA MULTI-FUENTE ---
if exist "test.pdf" goto skip_pdf

echo [INFO] Generando documento PDF de prueba (test.pdf)...
python -c "import fitz; doc = fitz.open(); page = doc.new_page(); page.insert_text((50, 50), 'El contrato legal', fontsize=12, fontname='helv'); page.insert_text((50, 70), 'tiene una consecuencia', fontsize=12, fontname='tiro'); doc.save('test.pdf'); doc.close()"

:skip_pdf

REM Crear __init__.py necesarios
if not exist "src\__init__.py" type nul > "src\__init__.py"
if not exist "src\font_matching\__init__.py" type nul > "src\font_matching\__init__.py"

REM --- EJECUCION DEL SISTEMA ---
echo [OK] Entorno listo. Iniciando sistema...
echo =======================================================
echo.

python src\pdf_translation\main.py --input test.pdf --output test_translated.pdf --source es --target en --generate-font-report

echo.
echo =======================================================
echo [INFO] Proceso finalizado.
pause