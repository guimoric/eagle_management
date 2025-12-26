@echo off
setlocal enabledelayedexpansion

:: Normalize ROOT to this script folder
set "ROOT=%~dp0"
pushd "%ROOT%"
set "ROOT=%CD%"
popd
set "VENV=%ROOT%\.venv"
set "EAGLE_GIT_ROOT=%ROOT%"

echo [pull] Updating repository at %ROOT%...
if exist "%ROOT%\.git" (
  git -C "%ROOT%" pull
) else (
  echo [pull] WARNING: no .git found at %ROOT%; skipping pull.
)

if not exist "%VENV%" (
  echo [venv] Creating virtual environment...
  py -m venv "%VENV%"
)
call "%VENV%\Scripts\activate.bat"

echo [deps] Installing/updating dependencies...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV%\Scripts\python.exe" -m pip install -e "%ROOT%"

pushd "%ROOT%"
echo [run] Starting server at http://127.0.0.1:8000 (Ctrl+C to exit)...
start "" "http://127.0.0.1:8000"
uvicorn eagle_pm.app.main:app --host 127.0.0.1 --port 8000
popd

echo [git] Checking changes...
if exist "%ROOT%\.git" (
  git -C "%ROOT%" status --porcelain | findstr /r "."
  if %ERRORLEVEL%==0 (
    for /f "tokens=1" %%i in ('"%VENV%\Scripts\python.exe" - <<PY
import datetime
print(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
PY') do set "COMMIT_MSG=%%i"
    git -C "%ROOT%" add .
    git -C "%ROOT%" commit -m "%COMMIT_MSG%"
    git -C "%ROOT%" push
  ) else (
    echo [git] Nothing to commit.
  )
) else (
  echo [git] No .git found; skipping commit/push.
)

echo [done] Finished.
endlocal
