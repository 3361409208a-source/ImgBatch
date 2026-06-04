@echo off
:: ImgBatch - Build EXE
cd /d "%~dp0"

set PYTHON=

:: Try python command
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    goto :found
)

:: Try py launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py
    goto :found
)

:: Try python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python3
    goto :found
)

:: Try common paths
for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "D:\pyenv-win-master\pyenv-win\shims\python.bat"
) do (
    if exist %%p (
        set PYTHON=%%p
        goto :found
    )
)

echo [X] 未找到 Python，请确认已安装 Python 并添加到 PATH
pause
exit /b 1

:found
echo  Python: %PYTHON%
echo  Building ImgBatch.exe ...
echo.
%PYTHON% build.py
pause
