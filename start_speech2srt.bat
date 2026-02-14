@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "INI_FILE=%~dp0speech2srt.ini"
set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"
set "FRONTEND_URL=http://localhost:3000"
set "BACKEND_PY="
set "BACKEND_CONDA_ENV="

if exist "%INI_FILE%" (
  set "CURRENT_SECTION="
  for /f "usebackq tokens=* delims=" %%L in ("%INI_FILE%") do (
    set "RAW_LINE=%%L"
    call :_parse_ini_line
  )
)

if defined BACKEND_PY (
  set "BACKEND_PY=!BACKEND_PY:"=!"
  set "BACKEND_PY=!BACKEND_PY:/=\!"
)
if defined BACKEND_CONDA_ENV (
  set "BACKEND_CONDA_ENV=!BACKEND_CONDA_ENV:"=!"
  set "BACKEND_CONDA_ENV=!BACKEND_CONDA_ENV:/=\!"
)

if not defined BACKEND_PY if defined BACKEND_CONDA_ENV set "BACKEND_PY=!BACKEND_CONDA_ENV!\python.exe"
if not defined BACKEND_PY if exist "%BACKEND_DIR%\venv\Scripts\python.exe" set "BACKEND_PY=%BACKEND_DIR%\venv\Scripts\python.exe"
if not defined BACKEND_PY set "BACKEND_PY=python"

if /I not "!BACKEND_PY!"=="python" (
  if not exist "!BACKEND_PY!" (
    echo [WARN] backend python not found: !BACKEND_PY!
    echo [WARN] fallback to PATH python.
    set "BACKEND_PY=python"
  )
)

if /I "!BACKEND_PY!"=="python" (
  set "BACKEND_CMD=if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && python run.py"
) else (
  set "BACKEND_CMD=""!BACKEND_PY!"" run.py"
)

start "speech2srt-backend" /D "%BACKEND_DIR%" cmd /k "!BACKEND_CMD!"
start "speech2srt-frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev"

timeout /t 4 /nobreak >nul
start "" "%FRONTEND_URL%"
exit /b 0

:_parse_ini_line
set "LINE=!RAW_LINE!"
for /f "tokens=* delims= " %%A in ("!LINE!") do set "LINE=%%A"
if not defined LINE exit /b 0

set "FIRST=!LINE:~0,1!"
if "!FIRST!"==";" exit /b 0
if "!FIRST!"=="#" exit /b 0

if "!FIRST!"=="[" (
  for /f "tokens=1 delims=]" %%S in ("!LINE:~1!") do set "CURRENT_SECTION=%%S"
  exit /b 0
)

if /I not "!CURRENT_SECTION!"=="runtime" exit /b 0

for /f "tokens=1* delims==" %%K in ("!LINE!") do (
  set "KEY=%%K"
  set "VALUE=%%L"
)

set "KEY=!KEY: =!"
for /f "tokens=* delims= " %%A in ("!VALUE!") do set "VALUE=%%A"

if /I "!KEY!"=="backend_python" set "BACKEND_PY=!VALUE!"
if /I "!KEY!"=="backend_conda_env" set "BACKEND_CONDA_ENV=!VALUE!"
exit /b 0
