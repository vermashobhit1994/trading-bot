@echo off
setlocal
cd /d "%~dp0.."

echo === Feature 8 smoke test (live demo API) ===
.\.venv\Scripts\python.exe cli.py smoke_test
exit /b %errorlevel%
