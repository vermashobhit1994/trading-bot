@echo off
setlocal
cd /d "%~dp0.."

echo === Feature 4 offline unit tests ===
.\.venv\Scripts\python.exe -m pytest tests\test_orders.py tests\test_models.py -v -m "not integration"
if errorlevel 1 exit /b 1

echo.
echo === Feature 4 live dry-run integration tests (requires .env) ===
.\.venv\Scripts\python.exe -m pytest tests\test_integration_feature4.py -v -m integration
exit /b %errorlevel%
