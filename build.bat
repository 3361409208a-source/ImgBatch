@echo off
:: ImgBatch - Build EXE
cd /d "%~dp0"
echo Building ImgBatch.exe ...
echo.
py build.py
pause
