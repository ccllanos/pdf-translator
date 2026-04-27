# Acotación Técnica: Estandarización de Entorno Python (BAT/VENV)

## Propósito

Asegurar que cada script de Python generado sea entregado como un paquete ejecutable y autónomo, eliminando la gestión manual de entornos virtuales y conflictos de versiones.

---

## 1. Instrucción Obligatoria

Siempre que generes código Python, deberás adjuntar un archivo iniciador de Windows (.bat) afín al modelo adjunto. Este archivo debe automatizar la creación del entorno virtual, la gestión de dependencias y la ejecución del script.

---

## 2. Requisitos del Archivo .BAT

El script .bat debe seguir esta lógica estructural:

### 2.1 Verificación de Versión
- Buscar una versión específica de Python (ej. 3.11) mediante el py launcher
- Validar que la instalación esté disponible antes de proceder

### 2.2 Gestión de VENV
- Crear la carpeta .venv si no existe
- Activarla automáticamente para el resto del proceso

### 2.3 Generación de Manifiestos
- Crear dinámicamente el archivo equirements.txt en tiempo de ejecución
- Incluir todas las librerías necesarias con sus versiones exactas

### 2.4 Congelación de Versiones (Pinning)
- Todas las librerías en el equirements.txt deben tener versiones exactas (usando ==)
- Garantizar la reproducibilidad del entorno en cualquier sistema

### 2.5 Archivos de Soporte
- Generar automáticamente un .gitignore básico
- Crear __init__.py si es necesario para paquetes Python

### 2.6 Punto de Entrada
- Ejecutar el script principal (por defecto pp.py)
- Mostrar mensaje de finalización y solicitar pausa

---

## 3. Modelo de Referencia (Ejemplificativo)

Utiliza la siguiente estructura como base, adaptando el nombre del proyecto y las librerías según el código que generes:

`atch
@echo off
setlocal
REM --- CONFIGURACION DEL ENTORNO ---
set PYTHON_VER=3.11
set VENV_DIR=.venv
set REQ_FILE=requirements.txt

echo [INFO] Verificando Python %PYTHON_VER%...
py -%PYTHON_VER% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Instala Python %PYTHON_VER% y el 'py launcher'.
    pause && exit /b
)

if not exist "%VENV_DIR%" (
    echo [INFO] Creando entorno virtual...
    py -%PYTHON_VER% -m venv %VENV_DIR%
)

call %VENV_DIR%\Scripts\activate

REM --- GENERACION DE RECURSOS ---
echo [INFO] Generando dependencias exactas...
(
  echo # LISTA DE VERSIONES PINNED
  echo libreria_ejemplo==1.0.0
) > %REQ_FILE%

if not exist ".gitignore" (
    echo .venv/ > .gitignore
    echo __pycache__/ >> .gitignore
)

REM --- INSTALACION Y EJECUCION ---
echo [INFO] Instalando librerias...
pip install -r %REQ_FILE% >nul
echo [OK] Entorno listo.
python app.py
pause
`

---

## 4. Consideración de Salida

No omitas este archivo por brevedad. La entrega se considera incompleta si el código Python no viene acompañado de su correspondiente automatizador de entorno y sus versiones de librería fijadas.

---

*Documento generado para el proyecto PDF Translator v1.2 - Traducción inteligente con preservación estricta de caracteres (1:1)*