@echo off
setlocal
pushd "%~dp0"
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Chua co moi truong du an. Hay chay lenh sau trong thu muc nay:
    echo uv sync --locked --extra dev
    popd
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -X utf8 -m streamlit run --server.headless=false "%~dp0app.py" %*
set "be_exit_code=%ERRORLEVEL%"
popd
exit /b %be_exit_code%
