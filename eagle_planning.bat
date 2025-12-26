@echo off
setlocal enabledelayedexpansion

:: Root (where this .bat lives)
set "ROOT=%~dp0"
set "VENV=%ROOT%\.venv"

echo [pull] Updating repository...
git -C "%ROOT%" pull

:: Create/use venv
if not exist "%VENV%" (
  echo [venv] Creating virtual environment...
  py -m venv "%VENV%"
)
call "%VENV%\Scripts\activate.bat"

:: Install deps
echo [deps] Installing/updating dependencies...
pip install --upgrade pip
pip install -e "%ROOT%"

:: Run app and open browser
pushd "%ROOT%"
echo [run] Starting server at http://127.0.0.1:8000 (Ctrl+C to exit)...
start "" "http://127.0.0.1:8000"
uvicorn eagle_pm.app.main:app --host 127.0.0.1 --port 8000
popd

:: On exit, commit/push if changes exist
echo [git] Checking changes...
if exist "%ROOT%\.git" (
  git -C "%ROOT%" status --porcelain | findstr /r "."
  if %ERRORLEVEL%==0 (
    set /p "COMMIT_MSG=Commit message [Autosave]: "
    if "!COMMIT_MSG!"=="" set "COMMIT_MSG=Autosave"
    git -C "%ROOT%" add .
    git -C "%ROOT%" commit -m "!COMMIT_MSG!"
    git -C "%ROOT%" push
  ) else (
    echo [git] Nothing to commit.
  )
) else (
  echo [git] No git repo found at %ROOT%.
)

echo [done] Finished.
endlocal
