@echo off
setlocal
cd /d "%~dp0.."

echo === Feature 3 automated tests (offline) ===
.\.venv\Scripts\python.exe -m pip install -q -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests\ -v -m "not integration"
if errorlevel 1 exit /b 1

echo.
echo === Feature 3 manual smoke tests ===
.\.venv\Scripts\python.exe cli.py validate_order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 2>nul
if errorlevel 1 exit /b 1

.\.venv\Scripts\python.exe cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run 2>nul
if errorlevel 1 exit /b 1

echo.
echo All Feature 3 tests passed.
