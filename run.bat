@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
set PYTHONUTF8=1

uv run streamlit run "1_📈_AutoChecker.py"

:: Пауза, чтобы окно не закрылось сразу при ошибке
pause
