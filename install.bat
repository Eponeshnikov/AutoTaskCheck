@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo === Установка AutoTaskCheck ===
echo.

:: 1. uv (менеджер Python и зависимостей)
where uv >nul 2>&1
if errorlevel 1 (
    echo [1/3] Устанавливаю uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
) else (
    echo [1/3] uv уже установлен
)
where uv >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: не удалось установить uv. Установите вручную: https://docs.astral.sh/uv/
    pause
    exit /b 1
)

:: 2. Python и зависимости в .venv
echo [2/3] Устанавливаю Python и зависимости...
uv sync
if errorlevel 1 (
    echo ОШИБКА: не удалось установить зависимости
    pause
    exit /b 1
)

:: 3. Ярлык на рабочем столе
echo [3/3] Создаю ярлык на рабочем столе...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d = [Environment]::GetFolderPath('Desktop');" ^
  "$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'AutoTaskCheck.lnk'));" ^
  "$s.TargetPath = '%~dp0run.bat';" ^
  "$s.WorkingDirectory = '%~dp0';" ^
  "$s.IconLocation = '%SystemRoot%\System32\shell32.dll,21';" ^
  "$s.Save()"
if errorlevel 1 (
    echo ОШИБКА: не удалось создать ярлык. Запускайте run.bat вручную.
) else (
    echo Ярлык AutoTaskCheck создан на рабочем столе
)

echo.
echo === Готово! Запуск: ярлык AutoTaskCheck или run.bat ===
pause
